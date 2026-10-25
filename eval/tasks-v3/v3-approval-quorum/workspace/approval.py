class Approval:
    def __init__(self, requester: str, roles: dict[str,str], required: dict[str,int]) -> None:
        self.requester, self.roles, self.required = requester, dict(roles), dict(required)
        self.status = 'pending'
        self.votes: dict[str,bool] = {}
        self.events: list[tuple[str,bool,str]] = []
    def counts(self) -> dict[str,int]:
        return {role: sum(v and self.roles[n] == role for n,v in self.votes.items()) for role in self.required}
    def audit(self) -> tuple:
        return tuple(self.events)
    def vote(self, name: str, approve: bool) -> str:
        if name not in self.roles: raise ValueError('voter')
        self.votes[name] = approve
        if all(self.counts()[r] >= n for r,n in self.required.items()): self.status = 'approved'
        self.events.append((name, approve, self.status))
        return self.status
