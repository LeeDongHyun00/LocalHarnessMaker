from dataclasses import dataclass
from typing import Iterable
@dataclass(frozen=True)
class Rule:
    role: str
    resource: str
    effect: str

class Policy:
    def __init__(self, parents: dict[str, list[str]], rules: list[Rule]) -> None:
        self.parents, self.rules = parents, rules
    def allows(self, roles: Iterable[str], resource: str) -> bool:
        for rule in self.rules:
            if rule.role in roles and rule.resource in (resource, '*'):
                return rule.effect == 'allow'
        return False
    def explain(self, roles: Iterable[str], resource: str) -> dict:
        raise NotImplementedError('explanation')
