# Prompt v1 prediction analysis

Source: read-only host report
`codex-bridge/report-copies/luna-calibration-2026-10-25-live2.txt`.
Both phases contain 40 schema-valid, identity-verified predictions. The existing
offline scorer reproduces the supplied counts. No live calls ran in this session.
Explanations below infer failure modes from outputs; they do not expose model
reasoning. Public calibration labels and scoring remain unchanged.

## Questions

Strict matching gives 4 TP, 7 FP, 16 FN. Of the 16 unmatched gold questions,
10 were not asked at all; 6 were asked but failed row-position or lexical matching.
All 20 gold questions belong to authored ambiguity extensions.

| Authored decision | Unasked cases | Asked but unmatched cases | Observed failure / v2 response |
| --- | --- | --- | --- |
| Sort key/direction | v1-01, v2-01 | none | Short appended instruction ignored; review every row and determine scope, key and direction without reopening specified ordering. |
| Normalization policy | none | v1-02, v2-02 | Questions correctly identify absent policy but refs are 8 vs 7 and 11 vs 9; avoid fragmenting rows and resolve refs after extraction. |
| Result limit | none | v1-03, v2-03 | First asks for a maximum without the scorer's `limit` anchor; second ref is 9 vs 8. Name the request's decision and keep coherent rows. |
| Rounding precision/mode | v1-04, v2-04 | none | No question despite absent precision/mode; require candidate readings with different outputs. |
| Invalid-record handling | none | none | Both asked and matched; preserve this coverage and state alternatives. |
| Serialized output format | v1-06 | v2-06 | Second asks the right decision but ref is 14 vs 9; distinguish return fields from serialization and retain compound specifications. |
| Timeout duration | v1-07, v2-07 | none | No value supplied and no question; an instruction to choose a timeout does not supply a universal default. |
| Duplicate policy | none | v2-08 | Ref is 10 vs 8; existing priority tie order does not necessarily answer duplicate handling. |
| Encoding policy | v1-09, v2-09 | none | Missing externally referenced policy overlooked; a reference to a required policy does not specify it. |
| Tie breaker | v1-10 | none | One omitted, one matched; determine whether any stated rule actually applies to the unresolved tie. |

Case IDs in this table end in `-ambiguity-variant`.

The 7 scorer FPs are: the 6 unmatched questions above (5 wrong row positions,
1 lexical mismatch), plus v2-05's question asking whether to create the explicitly
requested `../escape.py`. Only the latter is a new, unauthored decision. Path
safety belongs to code availability, not a confirmation question. Ten authored
decisions were recognized in the outputs, versus 4 passing the strict metric.
None of those questions stated two candidate readings as v2 now requires.

The v1 wording lacked an operational decision test, candidate alternatives and
an explicit pass over short appended instructions. V2 adds these while excluding
stated choices, conventional defaults and hypothetical implementation questions.
Examples illustrate choices without selecting an answer. This is a prompt
revision, not evidence that live precision/recall targets have been achieved.

## Requirement rows

Strict normalized span/kind matching gives 227 TP, 115 FP, 75 FN out of 302 gold
rows. Outputs repeatedly fragment a coherent specification at conjunctions or
semicolons, shorten source excerpts to commands/filenames, drop punctuation,
or label observable semantics as implementation constraints. Examples include
case sensitivity, preserving output newlines, domain field interpretation,
accepted empty inputs and tie order. `python verify.py` was sometimes classified
as non-test. These errors also shift question row references.

V2 keeps complete coherent specification sentences/lines, retains qualifiers,
action verbs and punctuation, and explicitly distinguishes observable behavior
from implementation restrictions. Test/verification intent determines kind even
for unsupported shell syntax. Every obligation remains required; no postprocessor
deletes rows to raise precision, and no scoring label is supplied to the model.

## Claims and citations

Strict claimed rows give 16 TP, 20 FP, 4 FN across 20 authored affirmative claims.
Sixteen FP rows actually over-attribute completion:

| Case | Extra claims | Failure |
| --- | ---: | --- |
| v1-05-public-excerpts | 5 | R-1's completion sentence reused for R-2 through R-5; `No check was run` attributed to R-6. |
| v1-10-public-excerpts | 1 | `No check was run` attributed to R-6. |
| v2-04-ambiguity-variant | 9 | Explicit incompletion/denial of completion attributed to R-1 through R-9. |
| v2-10-public-excerpts | 1 | `No check was run` attributed to R-7. |

The other 4 FP/FN pairs are excerpt-boundary errors in v1-03, v2-06, v2-07 and
v2-09 public-excerpt cases: correct R-1, but the affirmative completion prefix
was removed. Citations give 15 TP, 1 FP, 1 FN: v2-06 removed the cited path's
backticks. One assessment marked a bare citation supported without proof.

V2 separates affirmative completion attribution from support assessment, excludes
negations/plans/instructions, scopes explicit IDs, preserves actual blanket and
qualified completion, and copies complete completion clauses and exact citations.
A citation alone does not prove the asserted behavior. No deterministic repair
policy, public schema, model, effort or call budget changes.

## Pending host comparison

Use the same 40 cases per phase, selecting prompt v2. Targets: question precision
and recall each >= 0.6; claimed-row precision >= 0.7 and recall >= 0.8; row
precision >= 0.75 with recall no lower than 227/302. Report the unchanged strict
metrics alongside semantic/boundary distinctions. Prompt v1 is retained verbatim.
