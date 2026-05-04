# Difficulty Criteria — Objective Standards

This document defines what counts as "hard / error-prone / runtime-impacting". The main agent **should not judge difficulty by gut feel**; it should check items against this list one by one.

---

## I. Hard-difficulty checklist (matching any item satisfies condition (a))

### 1. Concurrency and async

- Any `asyncio` / `await` / `Promise.all` / goroutine / multithreaded write operations
- Use of locks, semaphores, condition variables, atomics
- Task cancellation, timeout propagation, context cancellation (`asyncio.CancelledError`, `context.Context`)
- Race condition possibility ≥ 0 (i.e., any shared mutable state)

### 2. Cross-process / cross-boundary communication

- IPC / message queues / pipes / WebSocket / SSE
- Cross-language calls (Python ↔ JS via stdout, Python ↔ Rust via FFI)
- Browser worker / service worker / postMessage
- gRPC, Thrift, custom binary protocols

### 3. Complex regex / string parsing

- Regex with lookbehind / lookahead / backreferences
- Regex matching nested structures (basically a wrong-tool signal — regex is bad at nesting)
- Hand-written parsers (any string processing with state)
- Unicode boundary handling (grapheme clusters, bidi, normalization)

### 4. Security-sensitive

- Auth / authz logic (JWT, OAuth, sessions, RBAC)
- Encryption / hashing / signature verification
- SQL / NoSQL / shell command construction (injection risk)
- User-uploaded file handling (path traversal, ZIP bomb, SSRF)
- CORS / CSP / XSS protection
- Code that consumes secrets (API keys, passwords, tokens)

### 5. State machines and protocols

- State machines with ≥ 4 states
- State transitions with side effects (DB writes, outbound requests, event emissions)
- Protocol handshakes, reconnect logic, idempotency guarantees
- Distributed transactions, Saga, TCC, eventual consistency

### 6. Advanced use of unfamiliar libraries

- First time using an advanced API of a library (not basic CRUD)
- Library version crosses a major release (API may differ entirely)
- Library is in alpha / beta (API may change)

### 7. Performance-sensitive (evidence-required, not threshold-only)

This category requires **concrete evidence**, not just structural hints, to avoid over-triggering on routine CRUD code that happens to have nested loops.

A task qualifies as performance-sensitive when **at least one of the following evidence items holds**:

- A profiler / benchmark / observed metric flags this code path as a hot spot
- Known data scale ≥ 1M rows / 1 GB at this code path (not project-wide)
- The user explicitly mentions a performance requirement ("< 100ms", "must handle 10k req/s")
- The code runs in a measurably constrained environment (Lambda cold start, embedded MCU, browser main thread for animation)
- Memory pressure is documented (`tech-decisions.md` flags this as memory-bound)

Structural hints (loop nesting depth ≥ 3, data structure size unknown, etc.) **are not enough on their own** — a normal CRUD service with a 3-level loop over small data is not a performance difficulty. Without one of the evidence items above, treat as ordinary work and skip the difficulty consultation.

### 8. Database schema / migrations

- Schema changes (add column, change type, add index)
- Migration script authoring
- Code involving transaction isolation level

### 9. Time zones / dates / floats

- Time zone conversion, DST
- Money calculation (must use Decimal, never float)
- Month-end / leap year / leap second handling

### 10. Browser / frontend runtime quirks

- Cross-browser CSS differences (especially Safari)
- iOS Safari quirks (viewport, keyboard, touch)
- React strict mode / Suspense / Server Components
- SSR / hydration mismatches

---

## II. Runtime-path determination (condition (b))

**Counts as runtime path:**
- Code that runs in production or staging
- Endpoints, buttons, commands the user can directly trigger
- Automated tasks / cron / webhook handlers
- Any library code that gets imported into runtime paths

**Does NOT count:**
- One-off data cleanup scripts (use once, throw away)
- Temporary experiments / exploration code
- Documentation example code
- Tools used only for local debugging (clearly marked `# debug only`)

---

## III. Impact-scope determination (condition (c))

**Counts as "impact ≥ 1 user-visible feature":**
- User login / signup / payment flow
- User data reads and writes
- Pages, API responses, push notifications the user sees
- Performance (response time, load time)
- Error displays

**Does NOT count:**
- Internal log format
- Backend admin tools (only used by internal team)
- Monitoring metric names (only affect dashboards)
- Code comments, documentation

---

## IV. Combined judgment template

When deciding whether to propose a debate, the main agent runs this template in thinking (English):

```
Difficulty check:
- (a) Hard point matched? [yes/no, which one from the checklist]
- (b) On runtime path? [yes/no, why]
- (c) User-facing impact? [yes/no, what feature]

Decision:
- If (a) AND (b) AND (c) all yes → propose three-way debate
- Otherwise → proceed solo
```

---

## V. Things that explicitly do NOT count as hard

Avoid being overly sensitive. The following do **not** trigger the proposal:
- Simple CRUD (no concurrency)
- Adding a normal field / route / button
- Writing tests (the test code itself)
- Editing copy / comments / formatting
- Calling a familiar library's common API
- Data format conversion (JSON ↔ dict and the like)

When in doubt, default to "not hard" and proceed solo. Debates have a cost; don't overuse them.
