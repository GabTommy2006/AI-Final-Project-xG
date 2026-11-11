"""Run tests and record actual validation evidence without retraining."""
from pathlib import Path
import unittest
from core import ROOT, save

if __name__=='__main__':
    suite=unittest.defaultTestLoader.discover(str(Path(__file__).parent),pattern='test_week4.py')
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    save(ROOT/'week4/results/validation.json',dict(passed=result.wasSuccessful(),tests_run=result.testsRun,
         failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped)))
    raise SystemExit(0 if result.wasSuccessful() else 1)
