"""Deterministic BM25 retrieval over a curated library of verified contracts."""

import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any

from controller.errors import InputError
from controller.generation import read_text, validate_input


def tokens(text: str) -> list[str]:
    return re.findall(r"\w+", text.casefold())


def retrieve_cases(request: str, directory: Path) -> list[dict[str, Any]]:
    """Read contract JSONL records and select up to three positive-score matches.

    Library owners curate passed contracts; schema validity alone never proves
    historical verification. This reader neither collects nor writes cases.
    """
    if not directory.is_dir():
        raise InputError("--cases must reference an existing directory")
    contracts: list[dict[str, Any]] = []
    seen: set[str] = set()
    for path in sorted(directory.rglob("*.jsonl")):
        for number, line in enumerate(read_text(path).splitlines(), 1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
                validate_input(value, "contract.schema.json")
            except (ValueError, TypeError) as exc:
                raise InputError(f"Invalid contract case: {path}:{number}") from exc
            identity = json.dumps(value, sort_keys=True)
            if identity not in seen:
                seen.add(identity)
                contracts.append(value)
    if not contracts:
        return []
    documents = [Counter(tokens(" ".join([case["task_summary"], *case["constraints"],
        *(item["description"] for item in case["success_criteria"])]))) for case in contracts]
    lengths = [sum(document.values()) for document in documents]
    average = sum(lengths) / len(lengths)
    if not average:
        return []
    frequencies = Counter(term for document in documents for term in document)
    query = set(tokens(request))
    scores: list[tuple[float, int]] = []
    for index, document in enumerate(documents):
        score = 0.0
        for term in sorted(query):
            frequency = document[term]
            if not frequency:
                continue
            idf = math.log(1 + (len(documents) - frequencies[term] + .5) / (frequencies[term] + .5))
            score += idf * frequency * 2.5 / (frequency + 1.5 * (.25 + .75 * lengths[index] / average))
        if score > 0:
            scores.append((score, index))
    return [contracts[index] for _, index in sorted(scores, key=lambda pair: (-pair[0], pair[1]))[:3]]
