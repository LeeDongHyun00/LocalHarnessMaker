# Evaluation preflight, 2026-10-21

Execution stopped under STOP-E4. The installed Codex diagnostic sandbox can read
the private grader outside the active task workspace. No executor or controller
model was called. This report contains no evaluation score or measured cost.

| Check | Evidence | Result |
| --- | --- | --- |
| Installed version | `codex --version` | `codex-cli 0.162.0-alpha.17.2` |
| Fixture validation | `.venv/bin/python -m pytest tests/eval -q` | 2 passed; buggy fixture fails all 3 private checks; reference correction passes all 3 |
| Read boundary | `.venv/bin/python eval/runner/check_isolation.py` | Exit 1; sandbox child exits 0 and prints `HIDDEN_GRADER_READABLE`; see `isolation.log` |
| Runtime effort evidence | No executor invocation | Not verified |
| Hooks under exec | `state/STATUS-plugin.md` is empty | Not verified; runner must remain independent of hooks |

The probe runs a Python read through `codex sandbox -P :workspace`, with its
working directory set to the fixture's `workspace/`. It reads the sibling
`hidden_tests/test_chunking.py` by absolute path and prints only a readability
marker. It does not reveal the test contents in the log. A sibling directory or
an unmounted-looking temporary workspace is therefore insufficient isolation
under this tested profile.

The diagnostic CLI requires `--permission-profile`; the first attempt using
only a legacy `sandbox_mode` override was rejected before execution. The final
probe uses the documented built-in profile. It is not an empirical test of
`codex exec --sandbox workspace-write`. No claim that a model saw the tests,
that every sandbox mode leaks, or that an evaluation task passed is made.

[Official permissions documentation](https://learn.chatgpt.com/docs/permissions)
states that permission profiles do not compose with legacy sandbox settings:
passing `--sandbox` selects the older settings unless managed profile rules
override them. A deny-read profile therefore requires its own installed-version
verification before it can protect the assigned executor command.

See `docs/decisions/0001-eval-isolation-proposal.md` for candidate fixes and
required evidence before resuming. The CLI runner, timeout/retry checkpoints,
metrics, pilot configuration and paid baseline remain unfinished.

## Assumptions

- The empty eval STATUS invokes the role's First task, not a future full run.
- The first fixture is hand-written Python with standard-library unittest
  grading; its metadata and expected files are provisional, not frozen shared
  schemas.
- A concrete read path under the built-in workspace sandbox is sufficient to
  trigger STOP-E4 before a paid experiment; the exact exec invocation remains
  unverified.
