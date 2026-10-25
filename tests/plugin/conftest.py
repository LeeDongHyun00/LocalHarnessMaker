"""Never discover or execute the host Codex from offline hook tests."""
from __future__ import annotations
import json
from pathlib import Path
import shutil
from typing import Any

import pytest
from plugin import versions


@pytest.fixture(autouse=True)
def fake_hook_version(monkeypatch: pytest.MonkeyPatch) -> None:
    # Historical tests explicitly exercise the retained interface; v3 tests
    # override this setting and test the production default separately.
    monkeypatch.setenv('HARNESS_INTERFACE_VERSION', '2')
    monkeypatch.setattr(versions, 'cli_version', lambda **kwargs: 'codex-cli 0.163.0-alpha.11.1')


@pytest.fixture(scope='session')
def amended_schema_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Keep the approved decision 0012 schema copy local to plugin tests."""
    from plugin.artifacts import ROOT
    root = tmp_path_factory.mktemp('plugin-amended-schemas')
    shutil.copytree(ROOT / 'schemas', root / 'schemas')
    path = root / 'schemas/pin-check.schema.json'
    amended: dict[str, Any] = json.loads(path.read_text())
    amended['properties']['model_evidence'] = {
        'type': 'object', 'additionalProperties': False,
        'required': ['source', 'observed_model', 'service_tier', 'observed_at',
                     'thread_id', 'evidence_sha256'],
        'properties': {
            'source': {'enum': ['listing', 'probe_observation']},
            'observed_model': {'type': 'string'},
            'service_tier': {'type': ['string', 'null']},
            'observed_at': {'type': 'string', 'format': 'date-time'},
            'thread_id': {'type': ['string', 'null']},
            'evidence_sha256': {'type': ['string', 'null'], 'pattern': '^[0-9a-f]{64}$'},
        },
    }
    amended['allOf'][0]['then']['required'] = ['model_evidence']
    path.write_text(json.dumps(amended))
    return root


@pytest.fixture(autouse=True)
def use_amended_pin_schema(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch,
                           amended_schema_root: Path) -> None:
    # Integration reads and writes must use the same amended schema as pin-check.
    # Imported ROOT constants for code, prices and example fixtures stay unchanged.
    if request.module.__name__.rsplit('.', 1)[-1] in {'test_pin_check', 'test_v3_hooks'}:
        from plugin import artifacts
        monkeypatch.setattr(artifacts, 'ROOT', amended_schema_root)
