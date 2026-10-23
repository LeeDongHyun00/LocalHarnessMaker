# Baseline C human preparation

The user fills each of the 20 files in c/ once, replacing every occurrence of
`__HUMAN_FILL__` with concrete guidance (or explicitly "None" when applicable).
Claude and other model agents must not fill these fields. Keep the task ID and
public prompt pointer. Use only that task's public prompt.md and public workspace.
Never look at private graders, references, or any run's results, logs or reports.
Do not revise any template after any baseline C run starts. Archive the original
filled files; the runner pins their SHA-256 and refuses changes on resume.

c-subset.json documents selection from the frozen 100 single-session tasks:
seed 0, exactly five per type and twenty distinct families. Reproduce selection
with `eval.tools.prepare_c.select(Path("eval/tasks"))`; the generation command
uses exclusive skeleton creation to protect human work. The static template
mirrors contract fields. C has no controller, verifier, re-instruction or handoff.
The runner appends it to day-1 input in the harness contract wrapper and position.
No fields have been filled by this preparation session.
