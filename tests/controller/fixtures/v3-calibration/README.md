# Hook prompt calibration v1

Each set has 40 requests: 20 derived from version 1 public prompt excerpts and
20 from version 2 public prompt excerpts. Each source contributes an unchanged
public-excerpt request and an authored ambiguity extension. Source paths and
SHA-256 identify the allowed public `prompt.md` files. No graders, task code,
evaluation runner or results were read. The user's 2026-10-25 instruction permits
this public material despite the older independent-only role prompt.

Requirements gold includes row kind, exact source span, text and expected
questions with nullable answers at artifact assembly. The question anchors and
row positions are authored scoring labels, never part of model input. Claims
use authored final responses, with present/missing/escaping/forged citations,
unsupported behavioral claims and embedded instructions. Expected assessments
are opinions about textual support; file hashes are verified separately in code.

The extraction scores are strict normalized source-span/kind matches, question
concept-anchor/row-position matches, claim excerpt/ID matches and citation exact
matches. Splitting differently can reduce scores; these lexical scores are not
human semantic judgments. Missing/malformed responses count as missed gold rows
and questions. Undefined precision/recall (zero denominator) is null. Gold
round-trip tests establish scorer mechanics only, never model quality.

Host preview (no calls):
`.venv/bin/python -m controller.measure_v3 --phase requirements --out /tmp/v3-requirements.json`

Host live measurement requires a current verified `pin-check.json`, `--live`
and `--i-have-approval`. The preview reports 40 calls and estimated USD 0.048
per phase (both phases: 80 calls / USD 0.096, not caps). Live targets and model
accuracy remain unmeasured. `--predictions FILE` scores previously collected
private-adapter outputs keyed by fixture ID without provider access.
