# Role 4: Verifier Engineer

Read AGENTS.md at the repository root first. This file is your contract.

## Goal

Build the verifier that compares what the executor model claims it did with what it actually did. The verifier is the core asset of the project. Mechanically checkable criteria are judged by code. Only llm_judge criteria are delegated to the judge CLI of Role 3. The verifier must stay independent from the control model: it never imports the controller package; it calls the judge CLI through subprocess only.

## Ownership

Owned paths: verifier/ including __main__.py (CLI), rules.py (command, file_exists, regex), claims.py (done-claim versus evidence), reinstruct.py (re-instruction message), handoff_validate.py, sandbox.py (isolated command execution). Tests in tests/verifier/.
Read-only: everything else.

## Interfaces

The two CLIs in AGENTS.md section 3.2: verifier check and verifier validate-handoff. Input: contract.json, --workspace, --transcript, --attempt. Output: verdict.json that validates against schemas/verdict.schema.json.

## Judgment rules

1. command: run in --workspace. Default timeout 120 seconds. No network. No writes outside the workspace. Compare the exit code and stdout with expected. Evidence: the command, the exit code, and the last 50 lines of stdout.
2. file_exists and regex: check the path and the pattern. Evidence: the path and the matching lines, at most 10.
3. llm_judge: call python -m controller judge. Record its status and reason unchanged and put the string llm_judge in evidence so that humans can review these items.
4. Done-claim verification (claims.py): from the last report in the transcript, extract claims of the form done, completed, implemented, passing, per criterion. If a claimed criterion fails its mechanical check, set status to fail and reason to claimed_without_evidence. This ratio is the source of the false-done-rate metric.
5. unverifiable: the command cannot run (missing dependency, missing path, and similar). Never treat it as pass. For the overall result, treat it like fail.
6. Re-instruction message (reinstruct.py): include only items whose status is not pass (fail or unverifiable), each with its number, description and one line of failure evidence. At most 300 characters. Form: "Items 3 and 5 are not done. Read the evidence below, fix only those items, then finish again." When attempt is greater than or equal to N, set reinstruct_message to null.
7. Contract quality warning: if success_criteria is empty or every item is llm_judge, print a warning on stderr and fill items with status unverifiable. A contract that cannot be verified must not pass.

## Deliverables

- D-1, due 2026-10-27: rules.py with the three rule types, verdict output, golden tests using the contract in schemas/examples/ for both the pass and the fail case.
- D-2, due 2026-11-03: claims.py, reinstruct.py, sandbox.py (timeout, no network, path restriction), complete CLI. Connected to the hooks of Role 2.
- D-3, due 2026-11-06: validate-handoff, llm_judge delegation, and the command python -m verifier sample --reports DIR --n 20 that extracts a sample for human review.
- D-4, due 2026-11-10: fixes for misjudgments found in the week 2 comparison, and the rules document verifier/RULES.md.

## Success criteria

- SC-1: each of the three rule types has unit tests for pass, fail and unverifiable.
- SC-2: on a fixture where the executor wrote done but the tests fail, claimed_without_evidence is produced.
- SC-3: a test enforces that the verifier package never imports the controller package.
- SC-4: the same input always produces the same verdict, except for llm_judge items.
- SC-5: a command that touches paths outside the workspace or contains destructive operations (for example rm -rf, writes to absolute paths) is not executed and is recorded as unverifiable with a reason.
- SC-6: a log line records the verifier execution time; the target is under 1 second excluding the time of the commands themselves.

## Verification

1. pytest tests/verifier
2. python -m verifier check --contract schemas/examples/contract.json --workspace tests/verifier/fixtures/ws_pass --transcript tests/verifier/fixtures/transcript_pass.jsonl --attempt 1 --out /tmp/v.json
3. The same command for the fixtures ws_fail and ws_claimed with their transcripts.

## Stop and escalate conditions

In addition to STOP-1 to STOP-4 in AGENTS.md:
- STOP-V1: the verdict schema needs an extra field. Write a proposal in docs/decisions/ and report.
- STOP-V2: the transcript format differs from docs/hooks-contract.md written by Role 2. Report it. Do not build a parser on guesses.
- STOP-V3: a dangerous command type that the sandbox cannot block is found. Report it.

## First task

1. Read the contract and verdict files in schemas/examples/. Implement the command rule in rules.py first.
2. Create three workspaces in tests/verifier/fixtures/: ws_pass, ws_fail, and ws_claimed (the transcript claims done but the tests fail), each with a matching transcript sample. Until docs/hooks-contract.md exists, assume the transcript is JSONL and record that assumption.
3. Update state/STATUS-verifier.md.
