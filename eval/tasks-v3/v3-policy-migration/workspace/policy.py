import copy

def migrate(data: dict) -> dict:
    return copy.deepcopy(data)
class Policy:
    def __init__(self, data: dict) -> None: self.data=data
    def allows(self, subject: str, action: str) -> bool:
        return action in self.data.get('users', {}).get(subject, [])
    def export(self) -> dict: return self.data
