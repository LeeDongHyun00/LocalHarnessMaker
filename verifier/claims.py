"""Extract explicit criterion claims from the measured Codex final report.

Only response_item/message records with assistant phase=final_answer are
reports (docs/hooks-contract.md, exec and TUI transcript excerpts). Tool output,
commentary, user messages and earlier reports cannot supply completion claims.
Claims use explicit IDs, bounded ID ranges, all-criteria statements or
distinctive description words sharing a clause with a completion predicate.
"""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import re
from typing import Any, Iterable, Mapping


_COMPLETE = re.compile(
    r"\b(?:done|complete(?:d)?|implemented|pass(?:ed|ing|es)?|met|satisfied|fulfilled|verified|succeeded|successful)\b",
    re.IGNORECASE,
)
_STATUS = re.compile(
    r"(?:done|complete(?:d)?|implemented|pass(?:ed|ing|es)?|met|satisfied|fulfilled|verified|succeeded|successful|success|ok|✓|✔|✅)",
    re.IGNORECASE,
)
_COLLECTIVE = re.compile(
    r"\b(?:all\s+(?:(?:of\s+)?the\s+)?(?:success\s+)?criteria|every\s+(?:success\s+)?criterion)\b",
    re.IGNORECASE,
)
_RANGE = re.compile(
    r"(?<![\w-])(?P<left>[A-Za-z][\w-]*?\d+)\s*(?:\bthrough\b|\bto\b|[–—]|\s-\s)\s*"
    r"(?P<right>[A-Za-z][\w-]*?\d+)(?![\w-])", re.IGNORECASE,
)
_COMMON = set("""a an the and or to of for from with without in on at by as is are was were be been
    being it its this that these those all each every success criterion criteria required requirement
    requirements must shall should can could will would has have had do does did ensure expected
    not no never incomplete unfinished unverifiable failed failing fails pending remaining blocked
    todo if file files exists exist output result results work task tasks""".split())
_NEGATIVE = re.compile(
    r"\b(?:not|no|never|incomplete|unfinished|unverifiable|fail(?:ed|ing|s)?|"
    r"pending|remaining|blocked|todo|will|would|should|could|if|cannot|unable|"
    r"(?:is|are|was|were|has|have|had|did|does|do|ca|wo|would|should|could)n['’]t)\b",
    re.IGNORECASE,
)
_EXCEPTION = re.compile(
    r"\b(?:except|but|other than|apart from|besides|excluding)\b", re.IGNORECASE,
)


def last_report(transcript: Path) -> str:
    report = ""
    for number, line in enumerate(transcript.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        record = json.loads(line)
        if not isinstance(record, dict):
            raise ValueError(f"transcript line {number} must be a JSON object")
        if "role" in record:
            raise ValueError("unsupported synthetic role/content transcript; use measured Codex records")
        if record.get("type") != "response_item":
            continue
        payload = record.get("payload")
        if not isinstance(payload, dict):
            raise ValueError(f"transcript line {number}: response_item payload must be an object")
        if (payload.get("type"), payload.get("role"), payload.get("phase")) != (
            "message", "assistant", "final_answer",
        ):
            continue
        content = payload.get("content")
        if not isinstance(content, list) or not content or any(
            not isinstance(part, dict) or part.get("type") != "output_text"
            or not isinstance(part.get("text"), str) for part in content
        ):
            raise ValueError(f"transcript line {number}: unsupported final report content")
        report = "\n".join(part["text"] for part in content)
    return report


def _words(text: str) -> list[re.Match[str]]:
    return list(re.finditer(r"\b[^\W_]+\b", text, re.UNICODE))


def _description_words(descriptions: Mapping[str, str]) -> dict[str, tuple[set[str], set[str]]]:
    vocabulary = {
        identifier: {m.group().casefold() for m in _words(description)
                     if len(m.group()) > 1 and not m.group().isdigit()
                     and m.group().casefold() not in _COMMON
                     and not _COMPLETE.fullmatch(m.group())}
        for identifier, description in descriptions.items()
    }
    counts = Counter(word for words in vocabulary.values() for word in words)
    return {identifier: (words, {word for word in words if counts[word] == 1})
            for identifier, words in vocabulary.items()}


def _references(
    clause: str, ids: list[str], identifier: re.Pattern[str],
    descriptions: dict[str, tuple[set[str], set[str]]],
) -> list[tuple[int, int, set[str]]]:
    references: list[tuple[int, int, set[str]]] = []
    ranges = list(_RANGE.finditer(clause))
    for match in ranges:
        left, right = match.group("left", "right")
        start, end = re.fullmatch(r"(.*?)(\d+)", left), re.fullmatch(r"(.*?)(\d+)", right)
        members: set[str] = set()
        if (left in ids and right in ids and start and end
                and start[1] == end[1] and int(start[2]) <= int(end[2])):
            for candidate in ids:
                numbered = re.fullmatch(r"(.*?)(\d+)", candidate)
                if (numbered and numbered[1] == start[1]
                        and int(start[2]) <= int(numbered[2]) <= int(end[2])):
                    members.add(candidate)
        # Even an invalid range occupies its span; do not claim an endpoint.
        references.append((match.start(), match.end(), members))
    for match in identifier.finditer(clause):
        if not any(start <= match.start() < end for start, end, _ in references):
            references.append((match.start(), match.end(), {match.group()}))
    words = _words(clause)
    present = {match.group().casefold() for match in words}
    for criterion_id, (vocabulary, distinctive) in descriptions.items():
        overlap = vocabulary & present
        if len(overlap) < min(2, len(vocabulary)) or not distinctive & present:
            continue
        matches = [match for match in words if match.group().casefold() in overlap]
        start, end = matches[0].start(), matches[-1].end()
        if not any(start < other_end and end > other_start for other_start, other_end, _ in references):
            references.append((start, end, {criterion_id}))
    for match in _COLLECTIVE.finditer(clause):
        references.append((match.start(), match.end(), set(ids)))
    return sorted(references, key=lambda reference: (reference[0], reference[1]))


def _clause_claims(
    clause: str, ids: list[str], identifier: re.Pattern[str],
    descriptions: dict[str, tuple[set[str], set[str]]], *, checked: bool = False,
) -> set[str]:
    parts = _EXCEPTION.split(clause, maxsplit=1)
    text = parts[0]
    references = _references(text, ids, identifier, descriptions)
    excluded: set[str] = set()
    if len(parts) == 2:
        excluded = set().union(*(ref[2] for ref in _references(parts[1], ids, identifier, descriptions)))
        # An unspecified exception cannot safely support an all-criteria claim.
        if not excluded:
            references = [ref for ref in references if not _COLLECTIVE.search(text[ref[0]:ref[1]])]
    if not references:
        return set()
    prefix = text[:references[0][0]]
    claimed: set[str] = set()
    pending: set[str] = set()
    for index, (start, _, members) in enumerate(references):
        pending.update(members)
        next_start = references[index + 1][0] if index + 1 < len(references) else len(text)
        predicate = text[start:next_start]
        if _NEGATIVE.search(predicate):
            pending.clear()
        elif _COMPLETE.search(predicate):
            if not _NEGATIVE.search(prefix):
                claimed.update(pending)
            pending.clear()
    if (_COMPLETE.search(prefix) or checked) and not _NEGATIVE.search(prefix):
        claimed.update(pending)
    return claimed - excluded


def extract_claims(
    report: str, criterion_ids: Iterable[str], descriptions: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Return claimed IDs and their first supporting, verbatim report clause.

    Description matching requires two content words (one for a one-word
    description), including a word unique among the supplied descriptions.
    It is lexical, case-insensitive matching, not semantic paraphrase inference.
    """
    ids = list(criterion_ids)
    if not ids:
        return {}
    identifier = re.compile(
        r"(?<![\w-])(?:" + "|".join(re.escape(i) for i in sorted(ids, key=len, reverse=True))
        + r")(?![\w-])"
    )
    vocabulary = _description_words({key: value for key, value in (descriptions or {}).items() if key in ids})
    claimed: dict[str, str] = {}
    fence: str | None = None
    status_column: int | None = None
    reference_columns: list[int] = []
    for line in report.splitlines():
        stripped = line.strip()
        marker = re.match(r"^(`{3,}|~{3,})", stripped)
        if marker:
            if fence is None:
                fence = marker[1][0]
            elif marker[1][0] == fence:
                fence = None
            continue
        if fence or stripped.startswith(">"):
            continue
        checkbox = re.match(r"^(?:[-*+]\s+|\d+[.)]\s+)?\[([ xX])\]\s+", stripped)
        if checkbox and checkbox[1] == " ":
            continue
        if "|" in stripped:
            cells = [cell.strip() for cell in stripped.strip("|").split("|")]
            headers = [cell.strip("*` ").casefold() for cell in cells]
            if "status" in headers or "result" in headers:
                status_column = headers.index("status") if "status" in headers else headers.index("result")
                reference_columns = [i for i, header in enumerate(headers)
                                     if header in {"id", "criterion", "criterion id", "description", "requirement"}]
                continue
            if all(re.fullmatch(r":?-+:?", cell) for cell in cells):
                continue
            column = status_column
            if column is None:
                column = next((i for i, cell in enumerate(cells) if _STATUS.fullmatch(cell.strip("*` "))), None)
            if column is not None:
                if column >= len(cells):
                    continue
                columns = reference_columns or [i for i in range(len(cells)) if i != column][:1]
                reference = " ".join(cells[i] for i in columns if i < len(cells))
                status = cells[column].strip("*` ")
                if _NEGATIVE.search(status) or not (_STATUS.fullmatch(status) or _COMPLETE.search(status)):
                    continue
                text = reference + " " + status
                for criterion_id in _clause_claims(text, ids, identifier, vocabulary,
                                                   checked=bool(_STATUS.fullmatch(status))):
                    claimed.setdefault(criterion_id, stripped)
                continue
        else:
            status_column = None
            reference_columns = []
        # Keep punctuation in evidence and never normalize or reconstruct it.
        for clause in re.split(r"(?<=[.!?])\s+|(?<=;)", stripped):
            clause = clause.strip()
            for criterion_id in _clause_claims(clause, ids, identifier, vocabulary, checked=bool(checkbox)):
                claimed.setdefault(criterion_id, clause)
    return claimed


def claimed_criteria(
    report: str, criterion_ids: Iterable[str], descriptions: Mapping[str, str] | None = None,
) -> set[str]:
    """Compatibility wrapper for callers needing only the claimed ID set."""
    return set(extract_claims(report, criterion_ids, descriptions))


def claim_observations(
    criteria: Iterable[Mapping[str, Any]], claims: Mapping[str, str], verdict: Mapping[str, Any],
) -> dict[str, Any]:
    """Join every real criterion to its observed claim and final verdict status."""
    statuses = {item["id"]: item["status"] for item in verdict["items"]}
    items = [{"id": criterion["id"], "claimed": criterion["id"] in claims,
              "clause": claims.get(criterion["id"], ""), "status": statuses[criterion["id"]]}
             for criterion in criteria]
    counts = Counter(item["status"] for item in items if item["claimed"])
    total = sum(counts.values())
    return {"items": items, "summary": {
        "claimed_items": total, "claimed_and_pass": counts["pass"],
        "claimed_and_fail": counts["fail"], "claimed_and_unverifiable": counts["unverifiable"],
        "unclaimed_items": len(items) - total,
    }}
