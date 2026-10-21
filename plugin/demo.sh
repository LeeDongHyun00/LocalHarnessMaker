#!/usr/bin/env bash
set -euo pipefail
plugin_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
project_dir="$(cd -- "$plugin_dir/.." && pwd)"
python_bin="${HARNESS_PYTHON:-$project_dir/.venv/bin/python}"
cd -- "$project_dir"
exec "$python_bin" -m plugin.demo "$@"
