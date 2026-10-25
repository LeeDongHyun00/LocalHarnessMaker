from pathlib import Path
import shutil
class CopyPlan:
    def __init__(self, source: Path, destination: Path) -> None:
        self.source = source
        self.destination = destination
        self.entries = tuple(sorted(p.relative_to(source).as_posix() + ('/' if p.is_dir() else '') for p in source.rglob('*')))
    def commit(self) -> Path:
        shutil.copytree(self.source, self.destination, dirs_exist_ok=True)
        return self.destination

def plan(source: str | Path, destination: str | Path) -> CopyPlan:
    return CopyPlan(Path(source), Path(destination))
