"""Keep synthetic runner runtimes and retained copies under pytest storage."""

from pathlib import Path
import tempfile

import pytest


@pytest.fixture(autouse=True)
def isolated_temporary_storage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Exercise production retention without leaving copies in system temp."""
    monkeypatch.setattr(tempfile, 'gettempdir', lambda: str(tmp_path))
