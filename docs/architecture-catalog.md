# Architecture Catalog

This catalog maps each lab to established software architecture patterns and separates concepts demonstrated by this repository from systems it does not implement. Each diagram under a lab's `architecture/` folder describes only its local code path unless a box is explicitly labeled as an external deployment option.

## Patterns across the labs

| Concern | Pattern to evaluate | Lab implementation | Production boundary |
|---|---|---|---|
| Context and memory | Retrieval pipeline; short-lived thread state vs cross-run store | Priority-ranked context packing, SQLite memory records with source, budget-aware task summary | No embedding model, vector DB, user tenancy, retention or model tokenizer |
| Tool contracts | Schema-first API boundary; request/response validation | Packaged JSON Schema Draft 2020-12 input/output contracts, strict JSON parser, duplicate-key rejection and explicit result envelope | Not an RPC framework, provider SDK or service endpoint |
| Authorization | Policy decision point (PDP) separated from policy enforcement point (PEP) | In-process allowlist checked before credential loader | Not OPA/Rego, IAM, OAuth, identity federation or a secret manager |
| Retries and budgets | Deadline-aware retries, exponential backoff, jitter, circuit breaker | Retry predicate, capped exponential delay, attempt/cost budget | No network transport, server `Retry-After`, jitter source, breaker or distributed budget |
| Idempotency | Idempotency key, durable result ledger, outbox/inbox boundary | SQLite transaction stores local operation result and checkpoints | Remote side effects still need provider idempotency/reconciliation; no outbox relay |
| Orchestration | Supervisor-worker; DAG/task queue; explicit contracts | Typed task envelope and handoff acceptance checks | No broker, durable queue, leases, worker pool or framework integration |
| Verification | Independent postcondition checks | Named checks gate completion | No attestations, signed artifacts, or deployment approvals |
| Evals | Golden regression set plus adversarial cases and metric reporting | Deterministic named eval cases and failure capture | No model judge, production dataset, statistical confidence or benchmark claim |
| Observability | Trace/span tree, structured events, metrics/log correlation | In-memory trace events, validated parent links and cost sum | Not OpenTelemetry SDK/OTLP export; no sampling, baggage propagation or backend |
| Recovery | Append-only event history and replay | JSONL state reconstruction with transition validation | Not a distributed durable workflow engine; no schema migration, leases, or replay-safe activity runtime |
| Sandbox | Isolation boundary and resource controls | Temporary workspace, subprocess timeout, bounded output retention | Not a security sandbox; use container/VM/OS controls for untrusted code |
| Economics | Router, response cache, fan-out, latency distributions | In-process deterministic primitives | No provider adapters, live TTFT, queueing telemetry or quality/cost benchmark |

## Deployment architecture choices

A **modular monolith** is a useful starting point when transaction boundaries and deployment ownership are shared. Split services only when independent scaling, ownership, failure isolation or regulatory boundaries justify the operational cost. The examples are deliberately local modules, not a microservice mesh.

A **hexagonal architecture** keeps domain decisions behind ports and adapters: tests inject fake clocks, sleepers, databases or tool functions, while production adapters would own HTTP, database, broker and model SDK details. The current labs use some dependency injection, but do not claim a complete hexagonal implementation.

An **event-driven workflow** can use a durable event history and replay to reconstruct orchestration state. Replayable workflow code must avoid uncontrolled nondeterminism; external I/O belongs in recorded activities/steps. The recovery lab validates a small JSONL event stream but does not implement Temporal's worker service, history store or replay contract.

A **CQRS/outbox** arrangement separates state changes from downstream event delivery. A local transaction can atomically write business state and an outbox row; a relay publishes rows and consumers deduplicate with an inbox key. The idempotency lab demonstrates only a local SQLite result ledger, not the distributed outbox protocol.

A **policy decision point/enforcement point** arrangement keeps policy decisions outside untrusted request text. The permissions lab demonstrates an in-process allowlist and proves denial occurs before credential loading. A real PEP must authenticate the caller and resource; an external PDP can be OPA or an organization's authorization service.

## Source references

These primary sources support architectural concepts; they do not imply this repository uses those products.

- [Temporal workflow replay and durable execution](https://docs.temporal.io/workflows#durable-execution)
- [LangGraph persistence: thread-scoped checkpoints and cross-thread stores](https://docs.langchain.com/oss/python/langgraph/persistence)
- [OpenTelemetry traces, spans, attributes and context propagation](https://opentelemetry.io/docs/concepts/signals/traces/)
- [Open Policy Agent: policy decision separation and Rego](https://www.openpolicyagent.org/docs/latest/)
- [JSON Schema: types and validation keywords](https://json-schema.org/learn/getting-started-step-by-step)
- [Kubernetes security context](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/)
- [AWS Builders' Library: timeouts, retries and backoff with jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/)
- [AWS Builders' Library: making retries safe with idempotent APIs](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/)
- [OpenAI function calling guide](https://developers.openai.com/api/docs/guides/function-calling)

## What the repository verified

The project test suite exercises deterministic local fixtures. It does not establish production throughput, security isolation, provider compatibility, or service-level objectives. See [the validation record](validation-record.md) for executable checks and observed outcomes.
