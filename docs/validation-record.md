# Validation Record

This file records outcomes produced by commands against the repository. It distinguishes observed test facts from design expectations.

## Current automated checks

Run from the repository root:

```powershell
python -m pytest -q
python -m compileall -q examples
python scripts/install_labs.py
python scripts/capture_demo_evidence.py
```

The pytest suite includes unit tests for invalid input, denial, retry exhaustion, idempotent replay, checkpoint persistence, handoff mismatch, postcondition failures, eval drift, trace relationships, event-log reconstruction and bounded subprocess output. `examples/test_demos.py` launches each monorepo demo as a subprocess. `examples/test_distributions.py` runs each independently installed namespace under isolated Python mode and invokes each installed console script.

The recorded execution before the current architecture expansion completed **99 tests successfully**, compiled all example modules, and reported no editor diagnostics. Subsequent local checks have also built all twelve wheels, installed them in a clean virtual environment, run all twelve console commands from outside the source tree, and completed the renderer tests. These are local results, not release certification. Rerun the commands above after changes to obtain current evidence.

`scripts/capture_demo_evidence.py` runs each installed lab console command and refreshes `examples/<lab>/evidence/run.json` and `demo-output.svg`. Run `scripts/install_labs.py` first. The SVG is a terminal-style image generated from captured stdout; timestamps and other runtime values may differ. The JSON record stores the portable command, exit code, stdout and stderr. It does not claim screenshots of a hosted UI or external platform.

## Failure cases observed during development

- A context-budget regression initially showed that summary packing could consume the space needed by a high-priority safety memory. The regression test failed before the ordering change and passed after memory-first packing.
- A retry test initially configured its predicate to retry every exception while asserting a non-retryable error would run once. Correcting the test predicate made the intended contract explicit.
- Python's subprocess timeout raises `subprocess.TimeoutExpired`; an initial assertion expected the built-in `TimeoutError` and was corrected to the actual API type.
- The Windows context demo initially left SQLite connections open when leaving a `with sqlite3.connect(...)` block. `contextlib.closing` now closes them, and the demo was rerun successfully.
- The sandbox output cap initially applied only after `subprocess.run(capture_output=True)` buffered all output. The implementation now drains pipes while retaining bounded bytes and reports truncation.
- The first clean evidence freshness check compared raw stdout against SVG text and failed on correctly escaped quotes. The check now compares against HTML-escaped stdout and validates every project capture.
- The first cross-project integration assertion indexed an already-unpacked result mapping. Correcting the assertion made the idempotent first/replay result comparison explicit.
- The first console-script capture run exposed two stale `module` references left after switching from module execution to installed entry points. Both error and success reporting now use the current project/command names.
- The observability demo originally printed raw event JSON with runtime timestamps. The trace data and JSONL export still retain timestamps, while the screenshot demonstrates deterministic event names and cost without runtime date noise.

These are observed implementation/test failures, not benchmark results or claims about external platforms.

## Verified packaging and architecture artifacts

- All twelve lab wheels built from the project directories.
- All twelve wheels installed in a fresh virtual environment; all twelve console commands ran from outside the source tree. The tool-contract wheel was inspected and contains both JSON Schema files.
- Twelve distinct Mermaid diagrams, twelve SVG captures generated from installed CLI stdout, and twelve JSON execution records are checked by repository tests.
- A local integration test composes schema validation, authorization, idempotency, completion checks and trace events. This does not exercise external services.
