# Tech Decisions Log

> Records project-local tech selections (models, algorithms, special techniques, trade-offs).
> Loaded by Step 0 to avoid re-deciding / walking back.
>
> **Field markers**:
> - **REQUIRED / 必填**: Decision content + Why this one (rationale)
> - **OPTIONAL / 可选**: Alternatives considered, Future maintenance notes, Risk points
>
> **Example placeholder cleanup**: any block marked `[Example — auto-remove on first real entry]` is removed by the skill the first time a real decision is recorded.

---

## Decision format

Each decision uses this structure (newest at top):

```
### [YYYY-MM-DD] Decision title

- **Decision** (REQUIRED / 必填): what was chosen
- **Context** (REQUIRED / 必填): where it's used / what problem it solves
- **Why this one** (REQUIRED / 必填): reasoning + trade-offs
- **Alternatives** (OPTIONAL / 可选): other options considered
- **Scope** (OPTIONAL / 可选): global / specific module
- **Related files** (OPTIONAL / 可选): code locations involved
- **Future maintenance** (OPTIONAL / 可选): things to watch if swapping it out
```

---

## Decision records

[Example — auto-remove on first real entry]

### 2026-XX-XX Chose httpx over requests for HTTP

- **Decision**: Use `httpx` instead of `requests` for HTTP client work
- **Context**: All outbound HTTP calls in the project
- **Why this one**: Need async support + a sync interface that matches; httpx feels closer to requests than aiohttp does
- **Alternatives**: requests, aiohttp, urllib3
- **Scope**: Whole project
- **Related files**: `src/clients/`
- **Future maintenance**: If switching back to requests, the async parts will need to be rewritten; the client layer is abstracted, so impact is contained

---

## Models / algorithms used — **OPTIONAL / 可选**

(LLM models, embedding models, classical algorithms, etc.)

| Module | Choice | Alternatives | Notes |
|---|---|---|---|
| | | | |

---

## Special techniques — **OPTIONAL / 可选**

(stdout IPC, pyodide, WebAssembly, cross-language bridges, unusual hacks)

| Context | Technique | Why this one | Risk points |
|---|---|---|---|
| | | | |

---

## Performance / resource decisions — **OPTIONAL / 可选**

(Batch size, concurrency level, timeout thresholds, memory caps)

| Parameter | Value | Where it's set | Reason |
|---|---|---|---|
| | | | |

---

## Deprecated approaches — **OPTIONAL / 可选**

(Things tried and abandoned — prevents re-trying the same idea later)

| Approach | Deprecated date | Why abandoned |
|---|---|---|
| | | |
