Run the test suite and report results:

```bash
python3 -m pytest tests/ -v
```

All 15 tests should pass. If any fail, read the failure output carefully, identify the
root cause in `main.py` or `tests/test_main.py`, fix it, and re-run.
