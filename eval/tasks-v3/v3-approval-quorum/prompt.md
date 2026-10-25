Implement Approval(requester, roles, required) in approval.py. roles maps eligible
voter names to one role each; requester is in that map. required maps role names
to positive integer vote thresholds (nonempty). These constructor inputs are
well-formed and copied so later caller changes have no effect. An approval is a
state machine exposing status ('pending', 'approved', 'rejected'), counts() (new
role-to-count dict for required roles), audit() (tuple of (name, approve, status)
entries), and vote(name, approve) returning the resulting status. approve is bool.

AQ1. Begin pending with zero counted approvals. Record at most one current vote
per voter. While pending a voter may replace their previous vote. An identical
repeat is a no-op, adding no audit entry. Count approvals by role and transition
to approved only when ALL required roles reach threshold; never count one voter
twice. An eligible rejection immediately transitions to rejected.
AQ2. The requester may vote and their vote appears in the audit. The product has
not decided whether their approval contributes to quorum. Apply the chosen
requester policy consistently in counts and state transitions. Their rejection
always vetoes, regardless of that policy.
AQ3. Each changed valid vote appends an audit entry with its resulting state, in
call order. Unknown voters raise ValueError('voter') before state/audit changes.
After either terminal state, EVERY vote attempt raises ValueError('closed'),
including duplicates/unknown voters. Returned dicts and constructor inputs cannot
be used to change internal state. There is no reset or persistence requirement.

Use Python 3.11+ and the standard library. Preserve the stated API. Change application
code and add regression tests as needed. Run `python -m unittest discover -s . -p "test_*.py" -v` from workspace/.
