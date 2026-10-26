# Design: compensating gpt-6.1-sol medium for everyday developers (2026-10-26)

Written by Claude for the user's review. Builds on docs/handoff/2026-10-26-sol-weaknesses.md. Nothing here is approved yet; section 8 lists the decisions.

## 1. Persona and constraints

The user is a developer who works in Codex interactively (CLI, IDE extension or desktop app) with gpt-6.1-sol at medium effort on the Standard tier, signed in with a ChatGPT plan. From that follow the constraints the system must respect:

| Constraint | Consequence for the design |
|---|---|
| The developer is present | Questions can be asked and answered; the system may ask instead of guessing |
| The developer often does not read long or difficult output and answers "continue" (user observation, 2026-10-26) | The developer is not a reliable safety check. A "continue" is never consent to a risky or wrong proposal; anything that needs a decision must fit in three plain lines; risky changes are stopped by code, not by the developer's reading |
| Medium on Standard is chosen for speed and plan usage | No extra model call by default; added wall time per turn under about 3 s, except running the project's own tests |
| It must work in any repository | Checks use the project's own test command and git state, configured once per project; no task-specific content |
| The developer will switch it off if it nags | Interventions only on evidence, at most one automatic continuation per turn, and a visible reason each time |
| Codex changes often (0.164.0-alpha.11.1 installed on 2026-10-26, up from 0.163) | Every hook event used is probed per CLI version before it is relied on |

## 2. Lessons carried over from versions 1 to 3

1. No weaker model in authority over Sol. Sol follows feasible instructions even when they are wrong, so a cheap controller's mistakes become Sol's mistakes (v2: 0.805 against 0.95).
2. Deterministic evidence first. Checks read the transcript, the exit codes and the repository; an LLM is used only where no deterministic signal exists, and then only to inform the developer, never to instruct Sol.
3. Never replace the developer's words. Rewritten prompts lose specifics (46 against 76 of 80); the system appends, it does not rewrite.
4. Intervene only where Sol actually fails. Sol already passes explicit single-session work (v3 A: 30 of 35 non-ambiguous tasks, v1 A 120 of 120 once the grader is corrected).
5. Verify the graders. The v1 false negatives passed mutation validation; every probe check is read against real outputs before it counts.

## 3. Target weaknesses, in priority order

| Priority | Weakness | Evidence (catalogue) | Why it matters to this persona |
|---|---|---|---|
| P1 | Premature completion: promise-then-stop, partial work declared done, unverified success claims | Public: #50771 and others, SC coding deception 1.50 percent; project: every real failure ended with "tests pass" | The developer has to notice and type "continue", or ships a defect |
| P2 | Self-confirming tests and regressions | W1, W7: own tests pass while an uncovered case or an old behaviour breaks | The developer trusts "tests pass" |
| P3 | Silent assumption under ambiguity | W2, public #56332, #53629 | Wrong behaviour that looks finished |
| P4 | Goal loss after compaction | Public #50771, #52424; a client double-counting bug before 0.164.0 | Long sessions are where developers lose the most time |
| P1b | Wrong proposals accepted unread | User observation: long or difficult output gets "continue"; project: Sol follows feasible wrong instructions | Combined with P1 and P5, the developer's "continue" turns a wrong proposal into shipped code |
| P5 | Acting on a wrong claim without checking it | Harness v1 and v2, paraphrased briefs | The developer's own wrong diagnosis gets implemented |
| Later | Rules quoted but not applied, needless approval pauses, scope creep, insecure code | Public reports only | Real, but less evidence or harder to check deterministically |

Out of scope: speed, cyber-policy false positives, model routing. These are service properties a harness cannot change.

## 4. Components

All components ship as one Codex plugin (hooks plus an AGENTS.md section plus one skill), opt-in per project.

| ID | Component | Hook | What it does | Targets |
|---|---|---|---|---|
| C1 | Completion gate | Stop | Reads the last turn from the session record. Blocks the stop, once, with a short continuation when (a) the final message announces work ("I'll", "next I will", "let me") and the turn made no tool call after it; (b) the message claims success ("pass", "verified", "done") but the last test command after the last edit exited non-zero or no test ran after the last edit; (c) the plan the model itself published still has open items and the message does not say why. Each block states the evidence in one line. A per-turn budget (1 continuation) prevents verification loops | P1 |
| C2 | Regression and coverage check | SessionStart, Stop | At session start, records the project test command's result as a baseline (cached by commit). At Stop after edits: tests that passed at baseline and now fail block the stop with their names; changed lines that no test executed (diff coverage) are listed in the completion note, not blocked | P2 |
| C3 | Assumption ledger | UserPromptSubmit, Stop | Appends one instruction to the developer's prompt: before editing, list choices the request leaves open that change behaviour; ask when the answer changes the implementation, otherwise state the default. At Stop, if code changed and the final message has no "Assumptions" line, one continuation asks for it. Sol writes the ledger itself; nothing judges it | P3 |
| C4 | Goal anchor | UserPromptSubmit, Stop, compaction signal | Stores the developer's requests verbatim (plus the decisions they confirmed) in a session file. When a compaction is detected in the session record, the anchor is re-injected at the next prompt or stop. Recommends Codex 0.164.0 or later | P4 |
| C5 | Check-the-claim rule | AGENTS.md section, UserPromptSubmit | When the developer states a cause, a location or an API as fact, Sol checks it against the code, logs or docs before acting and reports disagreement first. Pure instruction, measured by probes; promoted or dropped on the measurement | P5 |

| C6 | Short decisions | Stop | When the final message asks the developer something, it must fit a fixed shape: at most three lines, one question, plain words, a recommended option, and the concrete effect of each option (an input and what changes). A longer or multi-question message is sent back once to be shortened; the full explanation goes to a file the developer can open. Length and question count are measured, not judged | Unread output |
| C7 | "Continue" is not consent | UserPromptSubmit, PreToolUse | If the developer's reply to an open question is only a generic go-ahead ("continue", "ok", "진행해"), the system injects: take the reversible default, not the proposal. Changes that are hard to undo or that hide defects are blocked by code until the developer names them explicitly: deleting or moving files outside the change, git push, reset or history rewrites, dependency or schema changes, public API signature changes, and edits that weaken tests (removed assertions, new skip or xfail, broadened except, edited expected values next to a failing run). The block message is one line naming the action | Wrong proposals accepted unread |
| C8 | Evidence-bearing claims and undo | Stop, SessionStart | A proposal that states a cause ("the bug is in X") must cite a file and line or a command output; cited paths and line ranges are checked to exist. Before the first edit of each turn the workspace is checkpointed (a git stash-like snapshot, not a commit), so one command undoes a wrong turn the developer accepted without reading | Wrong proposals, hallucinated evidence |

Explicitly not built: an LLM judge of completion, an LLM rewriting the prompt, automatic effort changes.

## 5. How each component is proven

Measure before building. Step 1 is a baseline that shows which weaknesses reproduce at medium on Standard with the installed CLI; a component whose weakness does not reproduce is not built.

Probe set (new, small, held out from development):
- 30 to 40 multi-turn probes run through `codex exec` plus `codex exec resume`, with scripted developer turns, in throwaway repositories. Groups:
  - completion: long multi-step tasks, a correction mid-task ("that's wrong, fix X"), a task whose tests are slow;
  - regression: extend a working module whose old behaviour is pinned by hidden tests;
  - ambiguity: requests with one behaviour-changing open choice, where the scripted developer answers if asked;
  - compaction: sessions long enough to compact, with an early constraint that a late step must respect;
  - wrong claim: the developer names a wrong root cause, a non-existent API, or calls a correct test wrong;
  - wrong proposal: Sol is led toward a plausible but wrong fix (a misleading log, a test that "fails" for an environment reason) where the tempting next step weakens a test or changes a public API.
- The scripted developer is the realistic one: it answers every question with "continue" and never reads long output. An ideal developer who answers correctly runs as a second, smaller variant, so the gap between the two shows how much safety rested on reading.
- Each probe has a deterministic check of the outcome and of the weakness event (stop with zero tool calls, false success claim, silent assumption, violated early constraint, wrong claim followed). Every check is read against at least two real transcripts before it is frozen.
- Configurations: A (Sol medium, Standard, plain) and H (the same plus the plugin), same CLI version, 3 repeats per probe.
- Metrics: weakness-event rate per group, developer turns needed ("continue" count), task outcome, added wall time, tokens, and under the "continue" developer the rate at which a wrong proposal or a test-weakening edit reaches the final workspace. Decision messages are measured for length and question count. False interventions (a block whose evidence was wrong) are counted separately and must stay under 5 percent.

Success criterion, decided before any H run: H lowers the event rate of each targeted group by at least half with intervals reported, keeps the task outcome rate equal or better, adds at most 10 percent wall time and 5 percent tokens.

Then dogfood: the user develops with H for a few days; every intervention is logged with whether it helped.

## 6. Work split and schedule (development ends 2026-11-13)

| Dates | Work | Owner (CLAUDE.md roles) |
|---|---|---|
| 10/27 to 10/29 | Hook capability probe on 0.164 (which events fire, whether compaction is visible, whether Stop can continue); probe set authoring and check validation; baseline A | Role 2 probe, Role 5 probes, Claude runs and verifies |
| 10/30 to 11/04 | C1, C2 and C7 first, then C6, C8 and C3; each measured on its own probe group before the next | Roles 2 and 4 |
| 11/05 to 11/08 | C4 and C5 if their weaknesses reproduced; full A against H | Roles 2 and 5 |
| 11/09 to 11/13 | Dogfooding, analysis, final document with the negative results of v1 to v3 | Claude, user |

Role prompts and AGENTS.md need a Role 1 job to describe this direction before implementation starts.

## 7. Risks

- The completion gate's phrase patterns misfire on a different language or style; measured as false interventions, and the patterns are per-language data, not code.
- Running the full test suite at every stop is too slow in large projects; C2 then runs only the tests that import changed files, with the full run on request.
- Codex may not expose compaction to hooks; C4 then degrades to re-injecting the anchor on the developer's next prompt only.
- Hook trust: interactive Codex asks the developer to trust hooks.json once per project; installation must say so.
- The probe set is small; claims stay per group, with intervals.

## 8. Decisions for the user

1. Approve the persona constraints in section 1, especially "no extra model call by default".
2. Approve the priority order in section 3 and the rule that an unreproduced weakness is not built.
3. Whether to reuse the existing plugin hook runtime code (process hygiene, installer, version list) as plumbing, or start the plugin fresh. Reuse saves about two days; it does not carry over any v3 logic.
4. Approve the success criterion in section 5 before the baseline runs.
