# Agent Systems Lab

Twelve independently packaged Python labs for exploring reliability boundaries in tool-using systems. Each lab has a `pyproject.toml`, namespaced package, console command, tests, architecture diagram source, and captured demo evidence. The root monorepo runs all projects together.

## Examples

| # | Project | Demonstrates |
|---|---|---|
| 01 | [Context workbench](examples/context_engineering/README.md) | Budgeted assembly, SQLite memory, source provenance and summary priority |
| 02 | [Tool contract boundary](examples/tool_schemas/README.md) | Strict parsing, duplicate-key rejection and explicit errors |
| 03 | [Authorization boundary](examples/permissions/README.md) | Deny-by-default decision before credential access |
| 04 | [Retry budget lab](examples/retry_budgets/README.md) | Bounded retry predicate, capped delay and cost/iteration budget |
| 05 | [Idempotency ledger](examples/idempotency/README.md) | SQLite result ledger, replay and named checkpoints |
| 06 | [Handoff contract](examples/orchestration/README.md) | Supervisor-worker envelope and action/acceptance validation |
| 07 | [Completion gate](examples/verification/README.md) | Independent postconditions gate success |
| 08 | [Eval bench](examples/evals/README.md) | Categorized deterministic cases and failure capture |
| 09 | [Trace reading room](examples/observability/README.md) | Structured spans, parent links, JSONL and cost sum |
| 10 | [Run reconstruction](examples/recovery/README.md) | JSONL event replay with transition validation |
| 11 | [Trusted fixture runner](examples/sandbox/README.md) | Temporary subprocess, timeout and bounded output capture |
| 12 | [Routing and latency bench](examples/economics/README.md) | Router, cache, parallel calls and percentile utility |

## Quick start

Requires Python 3.11 or newer.

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[test]"
python scripts/install_labs.py
python -m pytest
```

Run an individual example from the repository root:

```powershell
python -m examples.context_engineering.demo
```

Each project can also be installed alone from its directory, for example:

```powershell
Push-Location examples\context_engineering
python -m pip install -e ".[test]"
context-memory-demo
Pop-Location
```

Other distributions and console commands are listed in each project metadata file. The root [architecture catalog](docs/architecture-catalog.md) maps patterns to established designs and their sources. The [validation record](docs/validation-record.md) documents observed test outcomes and failures. Projects use deterministic local fixtures and do not require external credentials or services.

## Safety boundary

These are engineering labs, not drop-in production infrastructure or implementations of Temporal, LangGraph, OPA, OpenTelemetry, Kubernetes, or a model provider. Their READMEs state what is implemented and what remains a production integration. In particular, the sandbox accepts trusted local fixtures only; it is not safe for untrusted code. Do not add real credentials to fixtures. External authorization, secret management, network policy, durable distributed execution and audit retention remain deployment responsibilities.

## Repository checks

```powershell
python -m pytest
python -m compileall -q examples
python scripts/install_labs.py
python scripts/capture_demo_evidence.py
```

CI installs each independent distribution and runs the test, compile and evidence-capture checks on Windows, macOS and Linux for supported Python versions. Contributions should include success, invalid-input and failure-recovery tests where applicable.

## Architecture and evidence

Start with the [architecture catalog](docs/architecture-catalog.md) for cross-cutting patterns and source references. Each lab README includes its own Mermaid architecture diagram, local run instructions, test evidence, observed failures or boundary notes, and a captured terminal-output image with a machine-readable run record. Regenerate those captures with `python scripts/capture_demo_evidence.py`; the records describe local demo runs only.

For deployment-level composition options and explicit non-implemented boundaries, see [Deployment Reference Architectures](docs/deployment-reference.md). The cross-project [reference-flow test](examples/test_reference_flow.py) exercises schema validation, authorization, idempotency, verification, and tracing together using local fixtures.
