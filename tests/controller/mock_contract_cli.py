"""Offline verification: run the real contract CLI with mocked HTTP only.

Use: python -m tests.controller.mock_contract_cli contract [normal CLI flags]
This helper never contacts a model or represents a live generation result.
"""

import io
import json
import os
import sys
from unittest.mock import patch
from urllib.request import Request

from controller.__main__ import main
from tests.controller.support import response


def mock_urlopen(request: Request, timeout: float) -> io.BytesIO:
    payload = json.loads(request.data or b"")
    assert payload["text"]["format"]["strict"] is True
    assert request.method == "POST" and timeout > 0
    return io.BytesIO(json.dumps(response()).encode("utf-8"))


def run() -> int:
    with patch.dict(os.environ, {"OPENAI_API_KEY": "offline-test-placeholder"}), patch(
        "controller.backends.cheap_api.urlopen", mock_urlopen
    ):
        print("OFFLINE MOCK: no model or network call", file=sys.stderr)
        return main()


if __name__ == "__main__":
    raise SystemExit(run())
