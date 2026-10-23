"""Public verification entry point. Run before claiming completion."""
import json
from pathlib import Path
import unittest

def main() -> int:
    suite = unittest.TestSuite()
    for name in ('test_public.py', 'test_regression.py'):
        suite.addTests(unittest.defaultTestLoader.discover('.', pattern=name))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    failures = len(result.failures) + len(result.errors)
    report = {'command': ['python', 'verify.py'], 'passed_tests': result.testsRun - failures,
              'failed_tests': failures}
    Path('verification.json').write_text(json.dumps(report, sort_keys=True) + '\n')
    return 0 if result.wasSuccessful() and result.testsRun >= 2 else 1

if __name__ == '__main__':
    raise SystemExit(main())
