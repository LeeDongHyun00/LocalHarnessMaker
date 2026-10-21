# Proposal: isolate private evaluation graders before executor runs

Author: Role 5, 2026-10-21. Status: proposed; no interface change approved or made.

STOP-E4 was triggered by the installed `codex-cli 0.162.0-alpha.17.2` diagnostic
sandbox. From the first task's `workspace/`, a process under the built-in
`:workspace` profile successfully read the sibling private test file by
absolute path. Evidence: `eval/reports/preflight-2026-10-21/isolation.log`.
No model was called and no task set was shared with Role 3.

The diagnostic profile is not direct runtime evidence for the role prompt's
`codex exec --sandbox workspace-write` invocation. It demonstrates that simply
copying a public workspace and keeping graders elsewhere on the host is not a
verified protection. A separate trusted grading phase is necessary.

| Candidate | Required proof and impact |
| --- | --- |
| Outer container or isolated worker; mount only public workspace and required runtime | Preserve the assigned exec flags. From every enabled executor tool, prove the grader source, repository, report directory and host session state are inaccessible. Run grading in a fresh copy only after executor termination. Verify persisted session resume without exposing grader artifacts. |
| Dedicated deny-read permission profile | Check installed-version support for every enabled tool. The official docs say `--sandbox` selects legacy settings, so changing the role's assigned invocation may be necessary. Role 1 must resolve any interface implications before implementation. |
| Separate host/account for grading | Verify executor cannot reach grader storage through filesystem, network, connectors or persisted state. Requires an agreed environment; no external configuration was changed. |

Before resuming the paid first-task run, record a successful public-workspace
read/write control, explicit grader-read denials, unchanged access controls
across resume, and a clean grading copy that is never exposed to a later
executor turn. Then confirm the exact exec flags and reasoning effort using
installed-version JSON event evidence. Role 2's hook behavior record and Role
1's evaluation-output schema decision remain pending dependencies.

This proposal does not alter schemas, CLIs, hooks, permissions or external
services. Role 5 stopped implementation and updated its own STATUS.

## Assumptions

- STOP-E4 applies when a concrete grader read path is found before a model run;
  actual model contamination is not required to halt.
- Choosing and provisioning a replacement isolation boundary is a follow-up
  decision after escalation, not authorized by this proposal itself.
