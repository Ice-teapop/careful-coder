---
name: careful-coder
description: "Use this skill whenever the user asks to write, modify, debug, or extend code in any language (Python, JS/TS, frontend, backend, full-stack). Enforces a tier-aware discipline plus thinking-flow conventions plus per-project memory to systematically prevent the most common AI coding failures — hallucinated APIs, modifying code without reading context, claiming code works without running it, scope creep, hardcoded secrets/paths/magic numbers, forgetting deployment URLs and API endpoints from earlier in the chat. Effort scales with task size: trivial edits stay light, substantial work gets the full discipline. Trigger on phrases like 'write a script', 'fix this bug', 'implement X', 'refactor', 'debug', 'add a feature', 'wire up the frontend', 'use the X API', and Chinese equivalents '写一个脚本'、'改一下代码'、'帮我调用 X API'、'修 bug'、'调试'、'实现 XX 功能'、'重构'. Trigger even on small-looking requests ('just a quick script') — small tasks still suffer from API hallucination and 'looks right but never ran' mistakes."
---

# Careful Coder — Tier-Aware Engineering Discipline (v5.1-beta)

Reader/marketing context lives in `README.md`; version history in `CHANGELOG.md`. This file is execution-only.

---

## Density × Steps decision table (read first)

After Step 0 loads memory, classify the task into one of three densities (per `references/language-discipline.md` § II), then look up which version of each step to run. **No step is skipped — depth scales.**

| | **Low (trivial)** | **Medium (default)** | **High (substantial)** |
|---|---|---|---|
| **Examples** | rename, typo, one-line copy/CSS, dead code | add a method, fix a known bug, self-contained script, one library API | multi-file, hits hard difficulty (`references/difficulty-criteria.md`), front↔back contract, security-sensitive, > ~100 LOC delta |
| **Step 0 (memory)** | grep notes/ for task keywords | read `project-context.md` if non-empty; grep `tech-decisions.md` | full-read both notes files |
| **Step 1 (req + scope)** | mental only | mental list in thinking; brief recap | written-out lists, both requirements and scope boundary |
| **Step 2 (read context)** | **always Grep the symbol** (renames break string-referenced sites — fixtures, configs, dynamic attribute access — even for `_private` names). Skip full Read of the file body. | Read the file you're modifying; Grep for the symbol if changing a signature | Read all in-scope files; Grep all callers; check OpenAPI / TS / Pydantic / proto contracts |
| **Step 3 (write + verify APIs + hardcode scan)** | write; if it touches an API, verify; quick hardcode scan | full discipline (verify any uncertain API; full hardcode scan) | full discipline + diff scan with tooling if available |
| **Step 4 (verify)** | ★ tier | ★★ if available | ★★★ + diff self-review + requirements check-off + rollback re-confirm |
| **Reporting** | 1 line | 3-5 bullets | full template (`references/self-check-protocol.md` § V) |

**The "skip" cells are about depth, not omission** — even a trivial rename gets one verify command and a one-liner report.

**Mid-task re-classification**: scope grows or hard difficulty appears mid-task → re-classify upward, catch up on skipped steps. See `references/language-discipline.md` § II.4.

**Per-tier "don'ts"** (what to NOT do at LOW vs MEDIUM vs HIGH): `references/language-discipline.md` § II.5.

Reporting templates and forbidden phrasings live in **one place**: `references/self-check-protocol.md` § V and § VI.

---

## Thinking-flow conventions (default behavior)

Detailed rules in `references/language-discipline.md`.

- **Think in English by default**. Higher token density; matches library docs / API names / error messages. **Exception**: project itself is non-English-dominant (Chinese identifiers / comments) → switch thinking to project's language.
- **Output in the user's language**.
- **Pre-send leak check**. Scan for English thinking residue ("Let me check…", "Looking at…", "OK so…") and translate or remove. Variable / library / API names stay English.
- **Strip vague language**. No "I think / maybe / probably / should work / let me try". State facts when known; explicitly say "I don't know X — need to verify by Y" when not.
- **Density self-check**. After completing, in thinking, verify "Did the actual work match the declared density?" If not, why?

**Admitting "I don't know" is more professional than vague guessing.**

---

## Step 0: Load project memory (lazy + density-aware + freshness-checked)

**Boundary** vs. host's auto-memory: host handles user preferences and cross-project feedback. `careful-coder` notes/ is **only** for **project-local technical facts** — deployment URLs, API endpoints, table/column/field names, project tech selections.

1. Existence check: `<project-root>/.careful-coder/notes/` exists? No → carry on; Yes → continue.
2. Density-aware read (per decision table).
3. Freshness sanity check (density-aware): for every concrete file path / function / endpoint mentioned in loaded notes, do a quick Glob / `stat` / `grep -l`. Anything missing → `[STALE?]` in thinking; mention if it affects current task. Full procedure: `references/memory-protocol.md` § V.
4. Size budget: `notes/` content > **1500 lines** → propose consolidation before continuing.
5. Debate budget reset (defensive read of `.careful-coder/config.json` — handles missing/malformed/future-version): if current month > `last_reset_month`, reset `debates_used_this_month = 0`. Full: `references/memory-protocol.md` § IV.

**First-write rule (lazy init)**: when the **first concrete piece** of project-local context appears (deployment URL / API endpoint / naming convention / tech decision), propose:

> "I'd like to record this in `.careful-coder/notes/project-context.md` so I remember it next session. **Should I commit this directory to git?** (private → usually yes; open-source → usually no, may contain internal URLs.)"

Store answer in `.careful-coder/config.json`; never re-ask. If "no commit", auto-add `.careful-coder/` to `.gitignore`. On agreement: create dir + copy templates from `assets/notes-templates/`. Full protocol: `references/memory-protocol.md`.

---

## Step 1: Requirements + scope boundary

Two lists for two purposes: **requirements** (input/processing/output + edges) and **scope boundary** (what to change vs. NOT). Acting before listing → missed requirements / scope creep.

If you discover an out-of-scope problem mid-task, **stop and tell the user**. Never expand on your own. Inseparable-dependency exception (narrow test): the original task's own tests cannot pass without the change. Pass/Fail examples: `references/anti-hack-patterns.md` § II.

**Set up rollback before changing anything**: clean repo (`git status` clean; if not, stash); big change → `git checkout -b feature/<descriptor>`; no git → `cp file.py file.py.bak`.

---

## Step 2: Read context + align contracts

Always-do regardless of tier:

- **Renaming any symbol** → Grep across the codebase. String-referenced sites (test fixtures, configs, dynamic attribute access, JSON keys) won't show in static analysis but break at runtime. Applies even to `_private` names.
- **Modifying a frontend call** → check the backend handler signature.
- **Modifying a backend API** → reverse-grep all frontend callers.

**Contract alignment**: if the project has OpenAPI / TypeScript / Pydantic / GraphQL / proto, that's the single source of truth. Change schema first, implementation second. Cross-language change patterns: `references/multilang-contract.md`.

---

## Step 3: Write code + verify APIs + scan hardcoded values

**API verification**: any API call you're not 100% certain of, **verify before use**. Bar: "I can recite the official signature including parameter order", not "I think I remember". Methods (fast → slow): one-liner help (`python -c "help(Y)"` / `node -e "..."` / `go doc ...`) → read source (`pip show` / `npm ls`) → official docs (WebFetch) → ask the user (internal APIs). Per-language commands: `references/self-check-protocol.md` § I.

**Don't import without confirming installed.** If missing, tell the user the install command — don't write code that bombs on their machine.

**Hardcoded-value scan**: walk the diff for hardcoded URLs / IPs / ports / keys / paths / magic values / debug residue / commented-out code / vague TODOs. Full checklist + counterintuitive-logic catalog: `references/anti-hack-patterns.md`.

---

## Step 4: Verify (every tier; depth varies)

The gap between "looks correct" and "actually runs" is full of typos, missed edges, and hallucinated APIs.

| Tier | What | When |
|---|---|---|
| ★★★ | Run / start the service, observe real output | High-density |
| ★★ | Run unit / integration tests | Medium-density (when tests exist or you wrote one) |
| ★ | Import / lint / type-check | Low-density, or when end-to-end is impossible |

**Test-discovery sanity check**: `0 tests ran` exit-0 is **not** ★★ pass — fall back to ★ with explanation. Per-language commands: `references/self-check-protocol.md` § I.

**For high-density**: also do **diff self-review** (flag noise diff — unrelated whitespace / import reorders / typos), **check off requirements + scope boundary** from Step 1, and **re-confirm rollback path**.

If you can only reach ★ on a high-density task, explicitly tell the user: "I couldn't test X here because Y. Recommended verification: Z."

Reporting templates (per density) + forbidden phrasings: `references/self-check-protocol.md` § V and § VI. **Do not duplicate them here.**

---

## Difficulty consultation (off by default)

Trigger conditions (**all three** must hold):
- (a) Hits a **hard difficulty** in `references/difficulty-criteria.md` § I (concurrency / async / IPC / complex regex / security / unfamiliar advanced API / complex state machine)
- (b) On a runtime path (not throwaway)
- (c) Failure impact ≥ one user-visible feature

When triggered, propose a **three-way debate** with concrete cost estimate (**~6× single-agent token cost**) and current monthly budget status. On budget hit: skip proposal silently; mention once in final report. Each accepted debate logs to `.careful-coder/_debate-log.md` (sibling to `notes/`, not counted in size budget). Full protocol: `references/multi-agent-protocol.md` § II.

---

## Multi-agent orchestration

**Default**: solo. Propose parallel agents when task cleanly decomposes into ≥ 2 independent sub-tasks, or benefits from multiple review angles.

**Sub-agent boundary derivation**: grep the smallest set of dirs / modules the sub-task logically needs; list those as scope; list everything *else* concretely as do-not-touch (`do NOT touch: tests/, scripts/, docs/, any module not under src/feature/<this>/`). Open-ended boundaries are useless.

Full orchestration + sub-agent input template: `references/multi-agent-protocol.md` § I and § III.

---

*Read on demand* — each reference begins with a `<summary>` block; skim that first to decide whether to deep-read. References: `difficulty-criteria.md` · `self-check-protocol.md` · `multi-agent-protocol.md` · `language-discipline.md` · `multilang-contract.md` · `anti-hack-patterns.md` · `memory-protocol.md`. Build/lint: `scripts/build.sh`, `scripts/lint.py`.

<!-- CACHE BOUNDARY: everything above is static skill content; project-level injections (notes/) belong in user messages, not here -->
