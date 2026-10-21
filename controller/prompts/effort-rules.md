# Executor reasoning effort rules v0

These deterministic heuristics describe the executor, not the control API's
reasoning settings. Model output cannot select an effort level.

| Feature | Points |
| --- | --- |
| Request UTF-8 byte bound <500 / 500–1999 / 2000–5999 / >=6000 | 0 / 1 / 2 / 3 |
| Distinct file references (path/name.extension), capped at three | 0–3 |
| test, tests, testing, pytest, unittest, or 테스트 appears | 1 |
| Requirement segments <3 / 3–5 / >=6 | 0 / 1 / 2 |

Segments split at newlines, semicolons, or sentence-ending punctuation followed
by whitespace. This is a reproducible proxy for distinct requirements; it does
not claim semantic understanding. File detection deduplicates matching strings
and can count a dotted hostname as a file. Negated test requests also match.

Scores 0–1 use low, 2–3 medium, 4–5 high, 6–7 xhigh, and 8–9 max. The rationale
records version, raw feature counts, and score. v1 calibration remains D-1 work.

`count_tokens` returns the UTF-8 byte count as a conservative text-only BPE
bound, not an exact tokenizer count; protocol framing is excluded. This avoids
inventing a tokenizer result or adding dependencies outside Role 3's scope.
Actual contract cost_estimate sums API-reported input and output tokens and
code-calculated USD across every generation, including failed validation calls.
Cached input is billed at its configured rate; reasoning output is not added
again. Missing usage accounting fails closed. A failed HTTP request logs null
token/cost fields because its billable usage is unknown.
