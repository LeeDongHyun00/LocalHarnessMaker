"""Check version comparability: python -m eval.runner.compare_versions REPORT REPORT."""

import json
from pathlib import Path
import sys

from eval.runner.report import require_same_codex_version


def main() -> int:
    """Accept report paths and refuse mixed versions before comparison."""
    try:
        if len(sys.argv) < 3:
            raise ValueError("Supply at least two report paths")
        version = require_same_codex_version([json.loads(Path(p).read_text()) for p in sys.argv[1:]])
    except (OSError, ValueError, KeyError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(version)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
