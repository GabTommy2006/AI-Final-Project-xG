"""Run Week 3 checks and save their actual result as report evidence."""
import unittest
from pathlib import Path
from pipeline import save

if __name__ == '__main__':
    suite = unittest.defaultTestLoader.discover(str(Path(__file__).parent), pattern='test_pipeline.py')
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    save(Path(__file__).parent/'results/validation.json', dict(
        passed=result.wasSuccessful(), tests_run=result.testsRun,
        failures=len(result.failures), errors=len(result.errors), skipped=len(result.skipped)))
    raise SystemExit(0 if result.wasSuccessful() else 1)
