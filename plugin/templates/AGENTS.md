# LocalHarnessMaker

When HARNESS_CONTRACT is injected, display its goal, checklist, assumptions,
reasoning effort and estimated cost, then wait for approve or edits before
changing files. Follow the harness skill. Run the contract verification commands
and report every criterion with evidence. Handle only unmet items when the Stop
hook re-instructs. HARNESS_HANDOFF records prior progress, not new approval.
Without a contract, work normally. Hook errors fall back to this skill workflow.
