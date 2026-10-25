from pathlib import Path
from typing import Callable
class Runner:
    def __init__(self, path: str | Path, perform: Callable, compensate: Callable) -> None:
        self.perform=perform
        self.jobs: dict = {}
    def run(self, job_id: str, steps: list[str]) -> dict:
        self.jobs[job_id]={'state':'succeeded','done':[{'step':s,'value':self.perform(s,s)} for s in steps]}
        return self.jobs[job_id]
    def export(self, job_id: str) -> dict: return self.jobs[job_id]
