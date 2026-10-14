#!/usr/bin/env python3
"""Validate preparation files; this never runs or scores development projects."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "experiments" / "pilot-v1"
ARMS = ("A", "B", "C", "D", "E")
PROJECTS = (("frontend-001", "frontend", "F"), ("backend-001", "backend", "B"))


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def inventory():
    paths = sorted(
        p for p in BUNDLE.rglob("*")
        if p.is_file() and p.suffix in (".json", ".md") and p.name != "hashes.json"
    )
    paths += [ROOT / "scripts" / "validate_pilot.py", ROOT / "requirements-preparation.txt"]
    return {
        str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in paths
    }


def validate():
    errors = []
    cards = {}

    def require(condition, message):
        if not condition:
            errors.append(message)

    for project_id, domain, prefix in PROJECTS:
        project = BUNDLE / "projects" / project_id
        card = read_json(project / "intent-card.json")
        cards[domain] = card
        require(card["project_id"] == project_id, f"{project_id}: mismatched project id")
        require(card["domain"] == domain, f"{project_id}: mismatched domain")
        identifiers = [r["id"] for r in card["requirements"]]
        expected = [f"{prefix}{i}" for i in range(1, len(identifiers) + 1)]
        require(identifiers == expected, f"{project_id}: nonsequential or duplicate requirement ids")
        critical = sum(r["critical"] for r in card["requirements"])
        require(2 <= critical <= 4, f"{project_id}: expected 2-4 critical requirements")
        require(4 <= len(card["user_decisions"]) <= 8, f"{project_id}: expected 4-8 user decisions")
        decision_ids = [d["id"] for d in card["user_decisions"]]
        require(len(decision_ids) == len(set(decision_ids)), f"{project_id}: duplicate decision ids")
        for decision in card["user_decisions"]:
            require(set(decision["requirement_ids"]) <= set(identifiers), f"{project_id}: unknown decision requirement")
        for requirement in card["requirements"]:
            require(bool(requirement["correction_feedback"].strip()), f"{project_id}: missing correction feedback")
            for scenario in requirement["acceptance"]:
                require(all(scenario[k].strip() for k in ("given", "when", "then")), f"{project_id}: empty acceptance step")

        common = (project / "common-context.md").read_text(encoding="utf-8")
        require(common.startswith(card["common_context"].strip()), f"{project_id}: common context differs from intent")
        metadata = read_json(project / "prompt-metadata.json")
        mentioned = metadata["mentioned_requirement_ids"]
        require(set(mentioned) == set(ARMS), f"{project_id}: missing prompt metadata")
        for arm in ARMS:
            text = (project / "prompts" / f"{arm}.md").read_text(encoding="utf-8").strip()
            require(bool(text), f"{project_id}: empty {arm} prompt")
            require(set(mentioned[arm]) <= set(identifiers), f"{project_id}: unknown {arm} requirement id")
            require(len(mentioned[arm]) == len(set(mentioned[arm])), f"{project_id}: duplicate {arm} requirement id")
        require(mentioned["A"] == mentioned["B"], f"{project_id}: A/B declared information differs")
        for arm in ("C", "D", "E"):
            require(set(mentioned[arm]) == set(identifiers), f"{project_id}: incomplete {arm} declared coverage")
        concise = (project / "prompts" / "C.md").read_text(encoding="utf-8").strip()
        candidate = (project / "technology-candidate.md").read_text(encoding="utf-8").strip()
        enhanced = (project / "prompts" / "E.md").read_text(encoding="utf-8").strip()
        require(enhanced == concise + "\n\n" + candidate, f"{project_id}: E must be exact C plus candidate")
        checklist = (project / "evaluation-checklist.md").read_text(encoding="utf-8")
        for requirement in card["requirements"]:
            require(f"## {requirement['id']}" in checklist, f"{project_id}: missing evaluation requirement")

    schema = read_json(BUNDLE / "authoring" / "intent-cards.schema.json")
    Draft202012Validator.check_schema(schema)
    for error in Draft202012Validator(schema).iter_errors(cards):
        errors.append(f"intent schema {list(error.path)}: {error.message}")
    prompt_schema = read_json(BUNDLE / "authoring" / "prompt-variants.schema.json")
    Draft202012Validator.check_schema(prompt_schema)

    policies = read_json(BUNDLE / "policies.json")
    runtime = read_json(BUNDLE / "runtime.json")
    provenance = read_json(BUNDLE / "provenance.json")
    require(runtime["candidate_limits"]["development_runs"] == 2 * 5 * runtime["candidate_limits"]["independent_repetitions"], "incorrect candidate run count")
    require(policies["question_policy"]["all_arms_can_ask"], "baseline questions must remain enabled")
    require(policies["correction_policy"]["no_new_features"], "corrections must not add features")
    require(policies["blinding_policy"]["artifact_content_must_not_change"], "blinding must preserve artifact behavior")
    require(not provenance["training_eligible"], "unexecuted preparation must not be training eligible")

    successful = {
        event["operation"] for event in provenance["generation_attempts"]
        if event.get("exit_code") == 0 and event.get("output_generated")
    }
    if provenance["actual_teacher_output"]:
        require({"intent_cards", "prompt_variants"} <= successful, "missing successful teacher generation records")
        require(runtime["model"]["successful_call_verified"], "teacher output requires verified call")
        for project_id, _, _ in PROJECTS:
            metadata = read_json(BUNDLE / "projects" / project_id / "prompt-metadata.json")
            require(metadata["source"] == "gpt-6.1-sol_teacher_output", f"{project_id}: inconsistent provenance")

    blockers = [name for name, ready in runtime["required_before_freeze"].items() if not ready]
    if not provenance["actual_teacher_output"]:
        blockers.append("actual_teacher_output_missing")
    if errors:
        for error in errors:
            print("ERROR: " + error, file=sys.stderr)
        return 1
    print(f"PASS: 2 intent cards, 10 prompts, {sum(len(c['requirements']) for c in cards.values())} requirements")
    print("These checks validate preparation structure, not information equivalence or project performance.")
    print("Freeze blockers: " + (", ".join(blockers) if blockers else "none"))
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-hashes", action="store_true", help="write draft checksum inventory")
    parser.add_argument("--check-hashes", action="store_true", help="verify existing checksum inventory")
    args = parser.parse_args()
    try:
        status = validate()
        if status:
            return status
        current = inventory()
        path = BUNDLE / "hashes.json"
        if args.check_hashes:
            saved = read_json(path)
            if saved["files"] != current:
                print("ERROR: checksum inventory differs from preparation files", file=sys.stderr)
                return 1
            print(f"PASS: {len(current)} SHA-256 entries")
        if args.write_hashes:
            record = {"status": "draft_checksum_inventory_not_protocol_freeze", "algorithm": "sha256", "files": current}
            path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"Wrote {len(current)} SHA-256 entries")
        return 0
    except (OSError, KeyError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
