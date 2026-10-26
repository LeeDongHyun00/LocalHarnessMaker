# CLAUDE.md - Claude Code as the project manager

Read AGENTS.md first. It defines the roles (Role 1 to Role 5), the repository ownership, the frozen interfaces, the working rules and the stop conditions. This file adds the division of labor between Claude and Codex.

## 0. Current state (2026-10-27)

AGENTS.md and docs/plan.md still describe the version 3 hook plan. The current direction is in docs/handoff/2026-10-27-persona-lab-pilot.md and overrides them until a Role 1 job updates them:
- No hooks. The deliverable is a skill set built on obra/superpowers v7.0.1 plus our additions (SP+), measured with persona experiments.
- The host is Windows. Codex: `%LOCALAPPDATA%\OpenAI\Codex\bin\<hash>\codex.exe` (newest hashed folder; not on PATH). Isolated CODEX_HOMEs need `-c windows.sandbox="unelevated"`, or Codex runs read-only.
- Experiment tooling lives in ../persona-lab (runner, cards, hidden checks) and ../codex-bridge (ops/codex_watch.py, Codex job briefs and reports). Both are outside the repository.
- Judging runs inside the Claude Code session with subagents, one per anonymized session bundle.
- Records and the running plan are kept on the project's Notion page.

## 1. Division of labor

- Claude (this Claude Code session): management, verification and final evaluation. Claude plans the work, dispatches it to Codex, checks the results, commits, pushes, keeps the documents current, and produces the final judgment of whether the project proved its claim.
- Codex (GPT-6.1 Sol through the local codex CLI): all implementation. Codex does the development work of Role 2 to Role 5 and the document writing of Role 1.
- The user: approvals (schema changes, cost, merges), decisions that AGENTS.md section 5 escalates, and the presentation.

Claude does not implement features itself. If Claude finds a bug, it writes a Codex job that fixes it. The exceptions are the three items in section 4 below.

Reason: the project measures how well a harness makes GPT-6.1 Sol work. Code written by Claude would not be evidence about Codex. Claude's independence is also what makes the final evaluation credible.

## 2. How to run Codex

The codex binary is not on PATH in a plain Terminal. Use /Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex (the bridge saves it in codex-bridge/codex-path.txt when started with --codex).

Codex version policy (user decision, 2026-10-22): the ChatGPT app updates the bundled CLI on its own, and the version may keep changing. Do not try to hold or roll back a version. Instead:
- record the installed version in every run (evaluation reports already carry metadata codex_version);
- compare only reports produced with the same version (SC-3); a comparison whose configurations ran on different versions is diagnostic only;
- when the version changes, rerun the hook compatibility probe (plugin/probe.py, exec mode) and a one-task audit compatibility smoke before any large run, and send any new native record types to Role 5;
- keep the history of versions and their probe evidence in plugin/ and docs/hooks-contract.md.
The first change was observed on 2026-10-22 at about 03:57 UTC: 0.162.0-alpha.17.2 became 0.163.0-alpha.11.1. All pilots so far ran on 0.162.0-alpha.17.2.

Two ways to run a job. Both reuse the Mac's ChatGPT login; no API key is needed.

### 2.1 Direct (preferred from Claude Code)

Run from the repository root. The prompt goes in on stdin.

    CODEX="$(cat ../codex-bridge/codex-path.txt)"
    "$CODEX" --no-daemon -a never exec --json --output-last-message /tmp/final.md \
      --model gpt-6.1-sol -c 'model_reasoning_effort="medium"' --sandbox workspace-write - < job-prompt.md

Continue a session: the same flags, then `resume SESSION_ID -` before the stdin prompt, with `-c 'sandbox_mode="workspace-write"'` instead of `--sandbox`. The session id is the thread_id in the first thread.started event of the JSON output.

### 2.2 Through the bridge

../codex-bridge/bridge.py polls ../codex-bridge/inbox/ for job files and writes results to ../codex-bridge/outbox/. Its README (Korean) documents the job format, the git_commit job type and the private grader root. Use it when a job should survive this Claude Code session, or when the user wants to watch progress from the chat app.

### 2.3 Facts about the Codex sandbox that shape every job

- .git is read-only inside Codex. Codex cannot commit. Every job prompt must ask for a final section named Commit plan (paths and a Conventional Commit message); Claude commits.
- Nested sandboxing is denied. Tests that need macOS seatbelt (tests/verifier/test_sandbox.py, six tests) and anything that calls codex exec from inside a job must run on the host, by Claude.
- Network is off inside jobs unless `-c sandbox_workspace_write.network_access=true` is passed. Do not pass it for development jobs.
- Nobody answers questions during a job. Jobs must be written so that a stop condition ends with a report, not a question.
- One Codex job per role at a time. Two jobs for the same role at the same time corrupt that role's files and STATUS.

### 2.4 Long host runs

Start every evaluation run and other long host process through ../codex-bridge/detach.sh LOGDIR -- COMMAND. It detaches the process (setsid, nohup) so that a Claude session restart cannot kill it; the 2026-10-23 restart killed two attached full runs. Resume a killed run with the same --out. After every push, confirm the GitHub CI run for that SHA.

## 3. The job prompt template

Every job prompt has this shape. Keep it in English, ASCII only.

    Read prompts/0N-ROLE.md and execute it, continuing from state/STATUS-ROLE.md, with this priority order set by the user:
    1. ...
    2. ...

    Environment for this session:
    - You run non-interactively through codex exec in a workspace-write sandbox. Nobody can answer questions. If a stop condition applies, stop and report it.
    - .git is read-only. Do not stage or commit. End your final report with a section named Commit plan: the exact paths to commit (your owned paths, your tests directory and your STATUS file) and a Conventional Commit message.
    - Network is disabled. Nested codex exec, live model calls and macOS sandbox-exec do not work here. Record such checks as pending host verification in your STATUS file.
    - Other roles may be working in this repository at the same time. Touch only your owned paths.
    - Update your STATUS file before you finish. Keep the final report short: what changed, test results with the exact command, what is pending.

Reasoning effort: high for Role 1 schema work and Role 4; medium otherwise; raise to high after a second failure on the same task.

Brief quality rules (added 2026-10-25 after the version 2 recovery day):
- Evidence, not paraphrase: when a job fixes something observed on the host, attach the verbatim records (native rollout lines, exec events, CLI output) in a read-only file under ../codex-bridge/report-copies/ and name it in the brief. Paraphrased symptoms produced wrong fixes twice.
- Length caps: the final report at most 40 lines; README and CHANGES edits limited to the behavior that changed; no restating of the brief. Claude reads every report, so verbosity is a direct cost.
- Parallel jobs: different roles run concurrently in their own worktrees (lhm-plugin, lhm-controller, lhm-verifier, lhm-r5-*, main for Role 1). Within one role, parallel jobs are allowed only on disjoint paths, with the shared files (STATUS, CHANGES, README, configs) left to a single consolidation job afterwards.

## 4. What Claude does after every job

1. Read the final message and the STATUS file of that role.
2. Verify the test claim on the host with the repository venv: `.venv/bin/python -m pytest tests/ROLE -q`. For Role 4 this includes the six sandbox tests that Codex could not run.
3. Check ownership: `git status --porcelain` must show only that role's paths, its tests directory and its STATUS file. Changes outside those paths are not committed; they go back to the role as a new job, or to the user if they look intentional.
4. Check for secrets: no API keys, no private grader paths, no grader contents in the repository.
5. Commit exactly the Commit plan paths with `git add -A -- PATHS` and `git commit -m MESSAGE -- PATHS`. Append the attribution lines the session requires.
6. Push `origin main` only. Never force-push, never rewrite history.
7. Record the host verification result in docs/weekly/ at the next integration review.

Claude may edit files directly only for: CLAUDE.md, docs/handoff/, and docs/weekly/. Host-operator tooling that Claude uses to dispatch, verify, scan, commit and watch (../codex-bridge/ops/) lives outside the repository and is written by Codex through an ops job; Claude runs it. Everything else goes through a Codex job for the owning role, including AGENTS.md, schemas/ and prompts/ (Role 1).

## 5. Evaluation duties (Role 5 produces data, Claude judges)

- Approve pilot costs: Role 5 runs a 10-task pilot per configuration and reports usage before any full run. Executor and control model both consume the ChatGPT subscription, so Claude checks plan usage (used_percent in the codex rate_limits events) and asks the user before a full run.
- Enforce isolation: the private grader root (LHM_PRIVATE_GRADERS) lives outside the repository, is never written in repository files, and is stripped from executor environments. Role 3 never reads eval/tasks/. Claude checks this at every integration review.
- Baselines must exist before the harness is judged: A (Sol medium alone), B (Sol max alone), C (static template). The claim is only proven if the harness beats A and B on cost per passing task with equal or better pass rate, and beats C by a margin that justifies the control model.
- The final evaluation is a document Claude writes in docs/evaluation/ from eval/reports/final/: numbers with sample sizes and confidence intervals, what was and was not verified by a human, and an explicit verdict.

## 6. Weekly rhythm

- Tuesday integration review (2026-10-27, 2026-11-03, 2026-11-10): Claude reads all five STATUS files, runs the full suite, writes docs/weekly/DATE.md, and lists scope cuts for the user. Codex's Role 1 job writes docs/plan.md and decision records; Claude writes the review itself.
- Development ends 2026-11-13. Presentation 2026-11-16. Drop the optional QLoRA item first if the schedule slips.
