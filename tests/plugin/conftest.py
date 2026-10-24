"""Never discover or execute the host Codex from offline hook tests."""
from __future__ import annotations
import pytest
from plugin import versions


@pytest.fixture(autouse=True)
def fake_hook_version(monkeypatch: pytest.MonkeyPatch) -> None:
    # Historical tests explicitly exercise the retained interface; v3 tests
    # override this setting and test the production default separately.
    monkeypatch.setenv('HARNESS_INTERFACE_VERSION', '2')
    monkeypatch.setattr(versions, 'cli_version', lambda **kwargs: 'codex-cli 0.163.0-alpha.11.1')
