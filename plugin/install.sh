#!/usr/bin/env bash
set -euo pipefail
# --check includes v3 exact-model/pricing preflight in install.py; it never
# changes Codex settings. Historical demonstrations explicitly select v2.
plugin_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec "${HARNESS_PYTHON:-python3}" "$plugin_dir/install.py" "$@"
