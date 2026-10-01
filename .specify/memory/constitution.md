<!--
Sync Impact Report:
- Version change: none (unfilled template) → 1.0.0
- Modified principles: none (first generation)
- Added principles:
  I. Version Control and Review
  II. Security and Secrets
  III. Observability
  IV. Versioned Contracts
  V. Specification Traceability
  VI. No Silent Divergence
  VII. Commit Messages
  VIII. Changelog Maintenance
  IX. Never Trust the Client
  X. Fail Gracefully and Predictably
  XI. Bounded Retry Over REST
  XII. Scalability and Peak Load
  XIII. Diagnosable Errors
  XIV. Tests Exercise Flows
  XV. Explicit Over Clever
  XVI. Contained Changes
- Added sections: Technology Stack and Constraints; Development Workflow and
  Quality Gates; Governance
- Removed sections: none
- Templates requiring updates:
  ✅ .specify/templates/plan-template.md — "Constitution Check" gate is
     derived from this file; no structural change needed
  ✅ .specify/templates/spec-template.md — no change; Principle V requires
     specs to open with the inheritance section
  ✅ .specify/templates/tasks-template.md — no change; Principle XIV drives
     flow-test tasks
- Follow-up TODOs (existing code vs. this constitution; not fixed here):
  - TODO(RETRY_4XX): `insights/core/requests.py::request_with_retry` retries on
    every `RequestException`, including 4xx raised by `raise_for_status()`,
    and hardcodes its wait time. Violates Principle XI.
  - TODO(STRUCTURED_LOGS): `LOGGING` in `insights/settings.py` uses a
    plain-text `verbose` formatter and no correlation identifier is propagated
    across HTTP, Celery, and EDA consumers. Violates Principle III.
  - TODO(SENTRY_CONTEXT): `sentry_sdk.init` sets no project/account/user/
    correlation context and `capture_exception` call sites add none.
    `User.USERNAME_FIELD` is `email`, so the opaque user identifier MUST be
    `User.pk`. Violates Principle XIII.
  - TODO(CI_FORMAT_GATE): `.github/workflows/ci.yaml` runs `black .` and
    `isort .`, which rewrite files instead of failing; they SHOULD run with
    `--check`.
  - TODO(COVERAGE_THRESHOLD): `.coveragerc` sets `fail_under = 70` while the
    pre-commit `check-coverage` hook declares `fail_under: 90` (not a valid
    pre-commit key, so it is ignored). Agree on one enforced threshold.
  - TODO(DEPENDENCY_AUDIT): no dependency vulnerability scan exists in CI.
    Required by Principle II.
  - TODO(BRANCH_PROTECTION): confirm GitHub branch protection on `main`
    (required review + green CI). It cannot be verified from the repository.
  - TODO(CHANGELOG_FORMAT): `CHANGELOG.md` uses ad-hoc `# Add` / `# Fix`
    headings rather than Keep a Changelog categories (Principle VIII, SHOULD
    for this service).
  - TODO(PRODUCT_SPEC_REPO): the product-spec repository that engineering
    specs inherit from is not recorded in this repository.

Provenance:
- Source: weni-ai/vtex-cx-engineering-constitutions (main)
- Bases: base-constitution.md, backend/base-constitution.md
- Domains: backend
- Generated: 2026-10-01 via setup-engineering
-->

# Insights Engine Constitution

Insights Engine is the Django/DRF backend that serves the Weni Insights
dashboards and data-analysis module. This constitution is the single source of
engineering policy for this repository. It combines the VTEX CX root
engineering constitution with the backend domain constitution and applies both
to this codebase. Where the two overlap, the root wins. The backend rules only
specialize it.

## Core Principles

### I. Version Control and Review

All code MUST enter `main` through a pull request on
`weni-ai/insights-engine`. A merge MUST require at least one approved review
and a green run of `.github/workflows/ci.yaml`. Direct pushes to `main` MUST be
blocked by GitHub branch protection. The local pre-commit `no-commit-to-branch`
hook SHOULD stay enabled as an early guard, but it does not replace platform
enforcement.

**Rationale:** the policy is only real when the platform enforces it, not when
it relies on trust. Peer review and a protected `main` keep history auditable
and stop unreviewed changes from reaching the tag-triggered production build.

### II. Security and Secrets

Secrets MUST never be committed. All credentials (`SECRET_KEY`, OIDC client
secrets, `JWT_SECRET_KEY`, VTEX/Meta/Nexus/GrowthBook tokens, `SENTRY_DSN`,
broker and database URLs) MUST come from an external secrets manager and be
injected at runtime as environment variables read through `django-environ` in
`insights/settings.py`. `.env` is for local development only and MUST NOT be
committed. The pre-commit `detect-private-key` and `detect-aws-credentials`
hooks MUST stay enabled. Access MUST follow least privilege by default: every
view, viewset, and internal endpoint grants only what its caller needs.
Dependencies MUST be installed only from trusted sources through Poetry with a
committed `poetry.lock`, and MUST be checked for known vulnerabilities.

**Rationale:** leaked credentials and untrusted dependencies are among the most
common and most damaging breaches. Preventing them is far cheaper than cleaning
up after them.

### III. Observability

Logs MUST be structured. They MUST never contain secrets (tokens,
`Authorization` headers, signed URLs) or sensitive personal data (user e-mails,
contact names, phone numbers, message content). Every log line MUST be emitted
through a module logger (`logging.getLogger(__name__)`), never through `print`.
Errors MUST be traceable across components through a correlation identifier.
That identifier MUST travel through HTTP requests, Celery tasks, EDA
consumers, and outbound calls to other services.

**Rationale:** structured, privacy-safe telemetry is what makes incidents
diagnosable without creating new data-exposure risks.

### IV. Versioned Contracts

Every public interface MUST be versioned following SemVer. In this service that
means:

- the REST API under the URL-version prefixes in `insights/urls.py` (`v1/`,
  `v2/`, `v1/internal/`)
- the OpenAPI schema produced by drf-spectacular at `/schema/`
- the payloads of events consumed or published through EDA

Changes MUST be backward compatible within a version prefix, or they MUST ship
with an announced deprecation path. A breaking change MUST introduce a new
version prefix (for example `v3/`) instead of altering an existing one. Silent
breaking changes MUST NOT be introduced. Release tags MUST follow SemVer
(`X.Y.Z`, with `-develop` / `-staging` suffixes for pre-production builds).

**Rationale:** the Insights frontend and other Weni services depend on stable
contracts. Explicit versioning and deprecation give them a predictable path to
adapt without outages.

### V. Specification Traceability

Every engineering spec (`specs/<###-feature>/spec.md`) MUST derive from exactly
one approved product spec. It MUST reference that spec through an immutable,
pinned version (commit or tag). A mutable URL or ID alone MUST NOT be used.
The product spec MUST exist and be tagged before its engineering spec is
created. An engineering spec MUST NOT redefine the "what" it inherits: problem,
scope, success criteria, and binding decisions belong to the product spec. A
technical architecture document SHOULD be produced for non-trivial features.
When one exists, the engineering spec MUST link to it, also pinned by commit or
tag. Its absence MUST NOT block the engineering spec.

Every engineering spec MUST open with an inheritance section in exactly this
format:

```
## Inheritance from Product Spec
- Product Spec: <title> — <URL>
- Pinned version: <commit/tag>
- Architecture doc: <none | URL + commit/tag>
- Inherited binding decisions: <short list>
- Scope of this spec: <slice implemented by this repo>
- Divergences: <none | link to amendment>
```

**Rationale:** traceability from product intent to technical execution keeps
decisions auditable. Pinning the version guarantees that every team implements
the same version of the feature, not divergent readings of a spec that changed
mid-flight. A mandatory product spec prevents engineering work without an
agreed problem. An optional architecture doc avoids blocking delivery when the
design is trivial. A single inheritance format keeps the link
machine-checkable.

### VI. No Silent Divergence

Sometimes a technical need contradicts something inherited from the product
spec: scope, success criteria, or a binding decision. That divergence MUST NOT
be implemented silently in code. It MUST be raised as an amendment in the
product repository and recorded in the `Divergences` field of the engineering
spec's inheritance section, with a link to the amendment. Once the amendment is
approved and tagged, the engineering spec's `Pinned version` MUST be updated to
that tag. A technical difference that contradicts nothing inherited is not a
divergence. It is an implementation decision, and it MUST be recorded in the
engineering spec.

**Rationale:** the product spec is the single source of truth. A silent code
deviation lets intent and implementation drift apart with no audit trail.
Routing divergences through amendments keeps the spec authoritative.

### VII. Commit Messages

Commits MUST follow the Conventional Commits format `<type>: <description>`.
Allowed types are `feat`, `fix`, `docs`, `refactor`, `test`, and `chore`. The
description MUST be imperative, specific, and at most 50 characters. Commits
MUST be atomic: one logical change per commit. This also applies to squash-merge
titles on `main`, which may carry a `(#<PR>)` suffix.

**Rationale:** Conventional Commits enable automated changelog generation and
semantic versioning. Atomic commits make bisecting, reverting, and reviewing
simpler.

### VIII. Changelog Maintenance

Public libraries MUST maintain a changelog in Keep a Changelog format. Every
user-facing change MUST appear in it under the right category (Added, Changed,
Deprecated, Removed, Fixed, Security), and version bumps MUST follow SemVer.
Insights Engine is a deployed service, not a public library, so this MUST
binds any library extracted from it. For the service itself, `CHANGELOG.md`
SHOULD receive an entry for every release tag, using the same categories and
the same SemVer number as the tag.

**Rationale:** a well-maintained changelog tells consumers what changed and
serves as release documentation. SemVer alignment sets predictable upgrade
expectations.

### IX. Never Trust the Client

Everything that reaches the server from outside MUST be treated as potentially
malicious, incomplete, or incorrect until it has been validated. That includes
the Insights frontend, Weni services calling `v1/internal/`, webhooks such as
GrowthBook, and EDA messages. Every external input (query parameters, request
bodies, path parameters, webhook and event payloads) MUST be validated for
type, format, range, and business rules at the server boundary before use.
Validation MUST go through DRF serializers or the module's `validators.py`.
Authorization MUST be enforced on the server for every request: authentication
(OIDC, JWT, or static token), DRF permission classes, and project-membership or
role checks scoped to the requested `project_uuid`. This holds even when the
client has already checked. Webhook signatures MUST be verified before the
payload is processed.

**Rationale:** clients run outside the server's control and can be inspected,
modified, or bypassed. Validating external input on the server is what
prevents injection, data corruption, cross-project data leaks, and privilege
escalation. Client-side checks alone can never stop them.

### X. Fail Gracefully and Predictably

Every external dependency will eventually fail. That includes PostgreSQL,
Redis, Elasticsearch, the Datalake SDK, the Chats, Nexus, Integrations, VTEX
and Meta APIs, and the message broker. Every call to an external dependency
MUST have an explicit timeout and MUST NOT block indefinitely. For `requests`,
that means every call passes `timeout=`. Failures MUST be handled explicitly
and returned as consistent, well-defined DRF error responses with an
appropriate status code. They MUST never surface as unhandled crashes, raw
upstream error bodies, stack traces, or other internal details.

**Rationale:** failure is a certainty, not an edge case. Handling it explicitly
keeps partial outages contained and observable. It stops one failing upstream
from taking down a dashboard, a worker, or a consumer, or from exposing
internals to callers.

### XI. Bounded Retry Over REST

When data moves between services over a REST call, a failure in that call MUST
be retried rather than dropped. A retry MUST happen only when another attempt
could plausibly succeed: a connection error, a request timeout, an HTTP 5xx, or
an HTTP 429. It MUST NOT happen on a 4xx that reflects a defect in the request
itself. A retry MUST only be applied to an operation that is idempotent or
protected by a deduplication key. If an operation is neither, it MUST be made
idempotent rather than left without retry. Every retry policy MUST define a
maximum number of attempts and a backoff strategy, and unbounded retry MUST NOT
be used. This applies equally to the shared helper
`insights/core/requests.py` and to Celery tasks, which MUST set
`max_retries` and a backoff when they use `autoretry_for`. When the attempts
run out, the failure MUST be logged and MUST remain recoverable (reported to
Sentry and re-runnable by a task or command). It MUST NOT be silently
discarded.

**Rationale:** propagation between services fails for transient reasons far
more often than for permanent ones, so retrying keeps services converging.
Resending a request the server rejected on its merits only adds load. Retrying
a non-idempotent operation duplicates its effect. Unbounded retry amplifies
load on a dependency exactly when it is already degraded. Keeping the exhausted
case recoverable prevents data from vanishing between two services that each
believe they succeeded.

### XII. Scalability and Peak Load

Every process type MUST be stateless so it can scale horizontally. That covers
the gunicorn/gevent web workers, Celery workers, Celery beat, and EDA
consumers. State that outlives a single request, task, or message MUST NOT be
kept in process memory (module-level mutable caches, globals) or on local disk.
It MUST live in a store shared by all instances: PostgreSQL, Redis (cache and
broker), or S3. The peak load a feature must sustain MUST be declared in its
engineering spec as a peak, not an average, and carried into the plan's
**Performance Goals** and **Scale/Scope** fields.

**Rationale:** capacity is a design input, not something to discover during an
incident. Dashboards are hit hardest during commercial peaks such as seasonal
sales, so sizing for the average guarantees failure exactly when it matters.
Statelessness is what makes adding instances a valid answer to load. Declaring
the peak turns scalability into a number that can be reviewed and tested.

### XIII. Diagnosable Errors

Every error reported to Sentry MUST carry enough context to be located and
filtered without reproducing it. At minimum that means the project identifier
(`project_uuid`), the account identifier (`org_uuid`, or `vtex_account` when
that is the relevant scope), the user identifier, and the request's correlation
identifier. All of these identifiers MUST be opaque. `User.USERNAME_FIELD` is
`email`, so the user identifier MUST be `User.pk`, never the e-mail address.
Sensitive personal data (names, e-mail addresses, phone numbers, government
identifiers, or contact and message content) MUST NOT be attached to an error
report under any circumstance. That includes Sentry user context, tags, extras,
breadcrumbs, and captured upstream response bodies.

**Rationale:** an error without identifying context can be counted but not
investigated. Opaque identifiers give an investigation exactly the filtering it
needs while keeping the report free of personal data, as Principle III
requires.

### XIV. Tests Exercise Flows

Every flow MUST have at least one test covering the complete use case, from
input to resulting effect. A flow can be an API endpoint, a Celery task, an EDA
consumer, or a report generation. Typical end-to-end tests:

- an `APITestCase` request through authentication, permissions, validation,
  use case, and serialized response
- a consumer test from message to persisted state

External services MUST be stubbed at the HTTP or SDK boundary (for example
with `responses` or mocks of the client class). Internal composition MUST NOT
be stubbed. Tests that assert a single method in isolation are allowed and
SHOULD be used for edge cases and input variations that are expensive to reach
through the whole flow. They MUST NOT be a flow's only coverage. Every flow
MUST cover its success path and its failure paths. Failure paths include
invalid input, unauthorized access, and upstream timeout or error. An error
path that no test exercises MUST NOT be considered covered.

**Rationale:** a suite made only of isolated method tests can be green while
the composition of those methods is broken. Method-level tests remain the
cheapest way to cover many inputs, so this rule adds to them rather than
replacing them. Failure paths matter most because they are the least exercised
in development and the most expensive in production.

### XV. Explicit Over Clever

What a piece of code does MUST be evident where it happens. Hidden side effects
and implicit control flow MUST NOT be introduced to save lines. That includes
signals that mutate unrelated state, overridden `save()` methods with remote
calls, and import-time work. Any literal that carries meaning MUST be a named
constant rather than an inline value. Examples are a threshold, a limit, a page
size, a timeout, a retry count, a cache TTL, or a unit conversion such as
cents. A literal with no meaning beyond its own value, such as an index of 0
or an increment of 1, is exempt. Current time MUST come from
`django.utils.timezone`, never from `datetime.now()` (enforced by the
`check-datetime-now` pre-commit hook). Comments MUST explain why a decision was
made: the constraint, the trade-off, or the non-obvious reason. A comment that
restates what the code already says is a signal to rewrite the code.

**Rationale:** code is read far more often than it is written, usually by
someone without the context that made the clever version feel obvious. An
unexplained literal is a decision nobody can review. Comments about the why
keep the information the code cannot carry, without creating a second
description of behaviour that silently goes stale.

### XVI. Contained Changes

A change MUST be limited to the context it was asked to address. Refactoring,
renaming, reformatting, or behaviour adjustments outside that context MUST NOT
ride along. Each belongs in its own change. This principle governs the scope of
a pull request as a whole. Principle VII (atomic commits) governs how that
change is divided internally, so a change that stays in scope MAY still span
several commits.

**Rationale:** a change that reaches beyond its stated scope is a change nobody
reviewed on purpose. It hides the intended fix among unrelated edits, makes the
diff expensive to read, and turns a revert into a choice between losing the fix
and keeping an unrelated regression.

## Technology Stack and Constraints

- **Language/runtime:** Python 3.10 (CI pins 3.10.13), dependencies managed
  with Poetry (`pyproject.toml` + `poetry.lock`).
- **Framework:** Django 5 with Django REST Framework. The OpenAPI schema is
  generated by drf-spectacular. Filtering uses django-filter.
- **Storage:** PostgreSQL (psycopg 3 with pool) as the system of record. Redis
  provides the cache, channel layer, and Celery broker/result backend. S3 holds
  generated files when `USE_S3` is enabled. Elasticsearch and the Weni Datalake
  (`weni-datalake-sdk`) are read sources.
- **Async work:** Celery with django-celery-beat for scheduled and background
  tasks. `weni-eda` handles event-driven consumers (RabbitMQ and Amazon MQ),
  under `insights/event_driven/` and per-app `consumers`.
- **Auth:** OIDC (`mozilla-django-oidc`), JWT (`pyjwt`), and static tokens for
  internal callers. Webhook verification uses `standardwebhooks`.
- **Feature flags:** GrowthBook through `weni-commons`.
- **Error tracking:** Sentry (`sentry-sdk` with the Django integration).
- **Serving:** gunicorn with gevent workers, packaged with `docker/Dockerfile`.
  Images are built and deployed from SemVer tags by
  `.github/workflows/build-insights-engine-push-tag-shared.yaml`.
- **Code layout:** each Django app under `insights/` holds its own `api/`
  (versioned views and serializers), `usecases/`, `services/`, `clients/` or
  `integrations/` for outbound calls, and `tests/`. New code MUST follow this
  layout. It MUST NOT add a parallel one.

## Development Workflow and Quality Gates

- Every PR MUST pass the CI workflow `.github/workflows/ci.yaml`. It applies
  migrations, runs `flake8`, `black`, and `isort`, then runs
  `coverage run manage.py test --parallel=auto`, `coverage combine`, and
  `coverage report`, which enforces the `fail_under` threshold in
  `.coveragerc`.
- Contributors SHOULD install the pre-commit hooks (`make pre-commit-install`)
  so that formatting, secret detection, `check-datetime-now`, and test-naming
  checks run before push.
- Schema changes MUST ship as Django migrations in the same PR as the code
  that needs them. Migrations MUST be safe to apply while the previous release
  is still serving traffic.
- Every Speckit plan (`specs/<###-feature>/plan.md`) MUST fill in its
  **Constitution Check** against Principles I–XVI. Any violation MUST be
  justified in **Complexity Tracking** before Phase 0 research begins.
- Reviewers MUST reject PRs that violate a MUST in this constitution unless the
  violation is recorded and justified in the related plan.

## Governance

This constitution supersedes any other engineering practice in this
repository. Its content derives from
`weni-ai/vtex-cx-engineering-constitutions` (root and backend bases). The root
base prevails over the backend base, and both prevail over the project layer.
Project-specific rules MAY add constraints but MUST NOT weaken a base MUST
without an explicit, justified exception written into the affected principle.

**Amendments** are made by pull request to `.specify/memory/constitution.md`.
Each amendment MUST update the Sync Impact Report at the top of this file and
receive at least one approved review. When a base constitution changes
upstream, this file MUST be regenerated or amended to match it.

**Versioning** of this document follows SemVer:

- MAJOR for removing or redefining a principle
- MINOR for adding a principle or section, or materially expanding guidance
- PATCH for clarifications and wording fixes

**Compliance:** every Speckit plan runs a Constitution Check against this
document. `/speckit-analyze` MUST report any conflict with a MUST as
CRITICAL. Code review MUST verify compliance for changes that touch the areas a
principle governs.

**Version**: 1.0.0 | **Ratified**: 2026-10-01 | **Last Amended**: 2026-10-01
