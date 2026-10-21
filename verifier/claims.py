"""Extract explicit criterion claims from the measured Codex final report.

Only response_item/message records with assistant phase=final_answer are
reports (docs/hooks-contract.md, exec and TUI transcript excerpts). Tool output,
commentary, user messages and earlier reports cannot supply completion claims.
Natural-language matching is conservative: an explicit criterion ID and a
completion word must share a clause. Unmapped prose is not inferred as a claim.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Iterable


_COMPLETE = re.compile(r"\b(?:done|completed|implemented|passing)\b", re.IGNORECASE)
_NEGATIVE = re.compile(
    r"\b(?:not|no|never|incomplete|unfinished|unverifiable|fail(?:ed|ing|s)?|"
    r"pending|remaining|blocked|todo|will|would|should|could|if)\b", re.IGNORECASE,
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


def claimed_criteria(report: str, criterion_ids: Iterable[str]) -> set[str]:
    ids = list(criterion_ids)
    if not ids:
        return set()
    identifier = re.compile(
        r"(?<![\w-])(?:" + "|".join(re.escape(i) for i in sorted(ids, key=len, reverse=True))
        + r")(?![\w-])"
    )
    claimed: set[str] = set()
    fenced = False
    for line in report.splitlines():
        if line.lstrip().startswith(("```", "~~~")):
            fenced = not fenced
            continue
        if fenced or line.lstrip().startswith(">"):
            continue
        # Commas separating a new criterion start a new claim; ID lists using
        # "and" remain together. Table rows and sentence boundaries also scope it.
        for clause in re.split(r"[.!;]|,\s*(?=" + identifier.pattern + r")", line):
            matches = list(identifier.finditer(clause))
            if not matches:
                continue
            prefix = clause[:matches[0].start()]
            pending: set[str] = set()
            for index, match in enumerate(matches):
                pending.add(match.group())
                end = matches[index + 1].start() if index + 1 < len(matches) else len(clause)
                predicate = clause[match.end():end]
                if _NEGATIVE.search(predicate):
                    pending.clear()
                elif _COMPLETE.search(predicate):
                    # A leading negation, e.g. "Not completed: SC-1", scopes
                    # the whole clause. Later criteria have their own predicates.
                    if not _NEGATIVE.search(prefix):
                        claimed.update(pending)
                    pending.clear()
            if _COMPLETE.search(prefix) and not _NEGATIVE.search(prefix):
                claimed.update(pending)
    return claimed
