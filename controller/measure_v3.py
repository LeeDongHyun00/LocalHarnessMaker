"""Score public-prompt calibration; optional explicitly approved, pinned host calls.

No evaluation implementation, task workspace or grader is opened. Gold labels
and provenance paths are excluded from model input. Default is a no-call preview.
"""

import argparse
import json
import logging
import sys
from collections.abc import Callable, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from controller.backends.base import Message
from controller.errors import BackendError, InputError
from controller.generation import read_text
from controller.settings import PACKAGE_DIR, load_object
from controller.v3 import _pin, atomic_json
from controller.v3_checks import digest
from controller.v3_client import MODEL, PinMismatch, PinnedLunaClient
from controller.v3_wire import CLAIMS, REQUIREMENTS

FIXTURES = PACKAGE_DIR.parent / "tests/controller/fixtures/v3-calibration"


def _norm(text: str) -> str:
    return " ".join(text.split()).strip().casefold()


def _metric(expected: list[Any], observed: list[Any],
            matches: Callable[[Any, Any], bool]) -> dict[str, Any]:
    """Maximum bipartite matching: duplicate predictions cannot earn double credit."""
    assigned: dict[int, int] = {}

    def assign(index: int, visited: set[int]) -> bool:
        for target, gold in enumerate(expected):
            if target in visited or not matches(gold, observed[index]):
                continue
            visited.add(target)
            if target not in assigned or assign(assigned[target], visited):
                assigned[target] = index
                return True
        return False
    for index in range(len(observed)):
        assign(index, set())
    true = len(assigned)
    return {"true_positive": true, "false_positive": len(observed) - true,
            "false_negative": len(expected) - true,
            "precision": true / len(observed) if observed else None,
            "recall": true / len(expected) if expected else None}


def score(cases: list[dict[str, Any]], predictions: dict[str, Any], phase: str) -> dict[str, Any]:
    row_gold: list[Any] = []
    row_observed: list[Any] = []
    question_gold: list[Any] = []
    question_observed: list[Any] = []
    claim_gold: list[Any] = []
    claim_observed: list[Any] = []
    citation_gold: list[Any] = []
    citation_observed: list[Any] = []
    errors: list[str] = []
    wire = REQUIREMENTS if phase == "requirements" else CLAIMS
    for case in cases:
        key = case["id"]
        value = predictions.get(key)
        valid = isinstance(value, dict) and Draft202012Validator(wire).is_valid(value)
        if not valid:
            errors.append(key)
            value = {"requirements": [], "open_questions": [], "claims": []}
        if phase == "requirements":
            row_gold.extend((key, row) for row in case["expected_rows"])
            row_observed.extend((key, row) for row in value["requirements"])
            question_gold.extend((key, q) for q in case["expected_questions"])
            question_observed.extend((key, q) for q in value["open_questions"])
        else:
            claim_gold.extend((key, c) for c in case["expected_claims"])
            claim_observed.extend((key, c) for c in value["claims"])
            citation_gold.extend((key, c["requirement_id"], cite["citation_excerpt"])
                                 for c in case["expected_claims"] for cite in c["citations"])
            citation_observed.extend((key, c["requirement_id"], cite["citation_excerpt"])
                                     for c in value["claims"] for cite in c["citations"])
    if phase == "requirements":
        metrics = {
            "rows": _metric(row_gold, row_observed, lambda a, b: a[0] == b[0] and
                            a[1]["kind"] == b[1]["kind"] and
                            _norm(a[1]["source_excerpt"]) == _norm(b[1]["source_excerpt"])),
            "open_questions": _metric(question_gold, question_observed, lambda a, b: a[0] == b[0] and
                                      a[1]["requirement_numbers"] == b[1]["requirement_numbers"] and
                                      all(anchor in _norm(b[1]["text"]) for anchor in a[1]["anchors"])),
        }
    else:
        metrics = {
            "claimed_rows": _metric(claim_gold, claim_observed, lambda a, b: a[0] == b[0] and
                                    a[1]["requirement_id"] == b[1]["requirement_id"] and
                                    _norm(a[1]["claim_excerpt"]) == _norm(b[1]["claim_excerpt"])),
            "citations": _metric(citation_gold, citation_observed, lambda a, b: a == b),
        }
    return {"sample_size": len(cases), "schema_valid": len(cases) - len(errors),
            "errors": errors, "metrics": metrics}


def measure(phase: str, *, predictions: dict[str, Any] | None = None,
            client_factory: Callable[[], Any] | None = None) -> dict[str, Any]:
    fixtures = FIXTURES / ("requirements.json" if phase == "requirements" else "claim-audit.json")
    cases = load_object(fixtures)["cases"]
    responses = dict(predictions or {})
    calls: list[dict[str, Any]] = []
    if client_factory is not None:
        for case in cases:
            inputs = ({"request": case["request"]} if phase == "requirements" else
                      {"requirements": case["requirements"], "final_message": case["final_message"]})
            prompt = PACKAGE_DIR / "prompts" / ("requirements-v1.md" if phase == "requirements" else "claim-audit-v1.md")
            messages: list[Message] = [{"role": "system", "content": read_text(prompt)},
                                       {"role": "user", "content": json.dumps(inputs, ensure_ascii=False)}]
            client = client_factory()
            status = "error"
            try:
                responses[case["id"]] = client.generate(REQUIREMENTS if phase == "requirements" else CLAIMS, messages)
                if client.model != MODEL:
                    raise PinMismatch("native model pin mismatch")
                status = "success"
            except Exception as exc:
                status = ("pin_mismatch" if isinstance(exc, PinMismatch) else
                          "timeout" if getattr(client, "timeout", False) else "error")
                responses[case["id"]] = None
            finally:
                usage = client.usage()
                calls.append({"case_id": case["id"], "status": status, "model": client.model,
                              "input_tokens": usage.input_tokens, "cached_input_tokens": usage.cached_input_tokens,
                              "output_tokens": usage.output_tokens, "usd": usage.usd,
                              "latency_seconds": usage.latency_seconds,
                              "native_events_sha256": digest(getattr(client, "events", "").encode())})
            if status == "pin_mismatch":
                break  # A failed identity pin disables further provider calls.
    result = score(cases, responses, phase)
    result.update(date=datetime.now(timezone.utc).date().isoformat(), phase=phase,
                  fixture_sha256=digest(fixtures.read_bytes()),
                  measurement="live_host" if client_factory else "supplied_predictions",
                  model=MODEL if client_factory else None, reasoning_effort="low" if client_factory else None,
                  calls=calls, predictions=responses,
                  total_usd=(sum(c["usd"] for c in calls) if calls and all(c["usd"] is not None for c in calls) else None),
                  scoring="Rows: exact normalized source span + kind. Questions: authored lexical concept anchors + row positions. Claims: exact normalized excerpt + ID. Citations: exact extraction. These metrics do not establish semantic equivalence.")
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("requirements", "claim-audit"), required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--predictions", type=Path)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--pin-check", type=Path)
    parser.add_argument("--i-have-approval", action="store_true")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stderr)
    try:
        if args.predictions is not None:
            if args.live:
                raise InputError("choose supplied predictions or live calls")
            result = measure(args.phase.replace("-", "_"), predictions=load_object(args.predictions))
        else:
            # Planning only: 6000 input and 1200 output tokens per case, no cache.
            print("40 maximum provider calls; planning estimate USD 0.048000 (not a cap).", file=sys.stderr)
            if not args.live or not args.i_have_approval or args.pin_check is None:
                print("No calls: host live measurement requires --live --pin-check FILE --i-have-approval.", file=sys.stderr)
                return 1
            pin = load_object(args.pin_check)
            _, prices, reference = _pin(args.pin_check.parent, pin["session_id"])
            result = measure(args.phase.replace("-", "_"),
                             client_factory=lambda: PinnedLunaClient(prices, reference))
        atomic_json(args.out, result)
    except (BackendError, InputError, OSError, ValueError) as exc:
        print(f"measure_v3: {type(exc).__name__}", file=sys.stderr)
        return 2
    print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
