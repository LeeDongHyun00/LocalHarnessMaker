"""Replace valid tasks with interruption-only missing usage using fresh sessions."""

from pathlib import Path
from typing import Callable

from eval.runner.process import ProcessResult, run_process
from eval.runner.rerun_invalid import main as _main, rerun_invalid


def rerun_unaccounted(private_root: Path, source: Path, out: Path, *,
                      execute: Callable[..., ProcessResult] = run_process,
                      version: str | Callable[[], str] | None = None) -> Path:
    """Regrade other tasks; retain replaced outcomes and costs in provenance."""
    return rerun_invalid(private_root, source, out, set(), execute=execute,
                         version=version, _unaccounted=True)


def main() -> int:
    """Use the recovery CLI conventions without changing existing flags."""
    return _main(_unaccounted=True)


if __name__ == '__main__':
    raise SystemExit(main())
