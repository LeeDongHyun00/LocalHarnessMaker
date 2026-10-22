#!/usr/bin/env bash
set -euo pipefail
plugin_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec "${HARNESS_PYTHON:-python3}" "$plugin_dir/install.py" "$@"
