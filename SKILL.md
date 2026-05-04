---
name: careful-coder
description: "Use this skill whenever the user asks to write, modify, debug, or extend code in any language (Python, JS/TS, frontend, backend, full-stack). Enforces a tier-aware discipline plus thinking-flow conventions plus per-project memory to systematically prevent the most common AI coding failures — hallucinated APIs, modifying code without reading context, claiming code works without running it, scope creep, hardcoded secrets/paths/magic numbers, forgetting deployment URLs and API endpoints from earlier in the chat. Effort scales with task size: trivial edits stay light, substantial work gets the full discipline. Trigger on phrases like 'write a script', 'fix this bug', 'implement X', 'refactor', 'debug', 'add a feature', 'wire up the frontend', 'use the X API', and Chinese equivalents '写一个脚本'、'改一下代码'、'帮我调用 X API'、'修 bug'、'调试'、'实现 XX 功能'、'重构'. Trigger even on small-looking requests ('just a quick script') — small tasks still suffer from API hallucination and 'looks right but never ran' mistakes."
---

# Careful Coder — Tier-Aware Engineering Discipline (v5.0-beta)

Applies to Python / JS / TS / frontend / backend / mixed-stack tasks: writing new code, modifying existing code, debugging.

> **v5 highlights** (full diff in `CHANGELOG.md`): debate-budget monthly reset wired up via Step 0 (was a documented-but-dead rule in v4); `_debate-log.md` moved out of `notes/` so it doesn't eat the size budget; mid-task density re-classification protocol explicit (`language-discipline.md` § II.4); freshness sanity check now scales with density (no 50× Glob calls on trivial tasks); `config.json` carries a schema `version`; size budget excludes skeleton lines (empty tables / placeholders) so it counts real content only; templates use bilingual REQUIRED/必填 + OPTIONAL/可选 labels; privacy guard documents what it does NOT auto-redact (project codenames / customer names / internal domains / Slack / Jira IDs); `scripts/build.sh` + `careful-coder.lock` give a reproducible build with drift detection.

---

## Why this skill exists

LLMs systematically fail at writing code in the following ways:

- **API hallucination**: inventing function names / parameters / libraries that look reasonable but don't exist
- **Skipping context**: editing unfamiliar code without reading it, breaking adjacent logic
- **Claiming code works without running it**: code looks right but was never executed
- **Declaring done while requirements remain unmet**: missing edge cases, missing items in the spec
- **Scope creep**: user asked for A, you "also fixed" B, C, D along the way
- **Hardcoding and counterintuitive shortcuts**: secrets/paths/magic numbers baked in, validation bypassed, debug residue left behind
- **Cross-turn amnesia**: forgetting deployment URLs / API endpoints / field naming conventions discussed earlier

This skill addresses these failures through **a tier-aware discipline, thinking-flow conventions, and a project-memory mechanism**. *Right effort for the task* is the principle; everything else follows.

---

## Density × Steps decision table (read this first)

After Step 0 loads memory, **classify the task into one of three densities** (per `references/language-discipline.md` §II), then look up which version of each step to run. **No step is ever fully skipped — but the depth of each step scales.**

| | **Low (trivial)** | **Medium (standard, default)** | **High (substantial)** |
|---|---|---|---|
| **Examples** | rename, typo fix, edit one line of copy/CSS, delete dead code | add a method to one file, fix a known bug, write a self-contained script, call one library API | multi-file change, hits a hard difficulty (`difficulty-criteria.md`), front↔back contract, security-sensitive, > ~100 LOC delta |
| **Step 0 (load memory)** | grep notes/ for keywords mentioned in the task; don't full-read | read `project-context.md` if non-empty; grep `tech-decisions.md` | full-read both notes files |
| **Step 1 (requirements + scope)** | mental only — no list in the report | mental list in thinking; brief recap in report | written-out lists, both requirements and scope boundary |
| **Step 2 (read context)** | **always Grep the symbol** (renames can break string-referenced sites — test fixtures, configs, dynamic attribute access — regardless of public/private). Skip the full Read of the file body. | Read the file you're modifying; Grep for the symbol if changing a signature | Read all in-scope files; Grep all callers; check OpenAPI/TS/Pydantic/proto contracts |
| **Step 3 (write + verify APIs + scan hardcoding)** | write; **if it touches an API, verify the API**; quick hardcode scan | full discipline (verify any uncertain API; full hardcode scan) | full discipline + scan diff with tooling if available |
| **Step 4 (verify)** | ★ tier (one import / lint / type-check command) | ★★ if available (run the script / run a test you wrote) | ★★★ + diff self-review + requirements check-off + post-change rollback path check |
| **Reporting format** | 1 line | 3-5 bullets | full template (see `references/self-check-protocol.md` §V) |

**Don't skip a step just because it looks small.** The "skip" cells above are about *depth*, not *omission* — even a trivial rename gets one verify command and a one-liner report.

**Mid-task re-classification**: if scope grows or a hard difficulty appears mid-task, re-classify upward and catch up on skipped steps. See `references/language-discipline.md` § II.4.

**Per-tier "don'ts"** (forbidden behaviors per tier — what to NOT do at LOW vs MEDIUM vs HIGH): see `references/language-discipline.md` § II.5.

The full per-tier reporting templates live in **one place**: `references/self-check-protocol.md` §V. SKILL.md does not duplicate them.

---

## Thinking-flow conventions (default behavior)

Detailed rules in `references/language-discipline.md`.

**Core points:**

- **Think in English by default**. Higher token density; matches the language of most library docs / API names / error messages. **Exception**: when the project itself is non-English-dominant (Chinese variable names / Chinese comments / Chinese-language documentation), switch thinking to the project's language to avoid translation overhead.
- **Output in the user's language**. Reply in whatever language the user wrote in.
- **Pre-send leak check**. Before sending, scan for English thinking residue (e.g., "Let me check…", "Looking at…", "OK so…") and translate or remove. Variable / library / API names stay English.
- **Strip vague language**. No "I think / maybe / probably / should work / let me try". State facts when you know; explicitly say "I don't know X — need to verify by Y" when you don't.
- **Density self-check**. After completing the task, in thinking, verify "Did the actual work match the declared density?" If not, why?

**Admitting "I don't know" is more professional than vague guessing.**

---

## Step 0: Load project memory (lazy + density-aware + freshness-checked)

**Why**: deployment URLs, API endpoints, field conventions discussed earlier are easy to forget. Load them once at task start.

**Boundary** (vs. host's auto-memory): the host already remembers user preferences and cross-project feedback. `careful-coder` notes/ is **only** for **project-local technical facts** — deployment URLs, API endpoints, table/column/field names, project tech selections.

### Loading procedure

1. **Check existence**: does `<project-root>/.careful-coder/notes/` exist?
   - **No** → don't auto-create. Carry on. (Templates only get copied in when Step "first write" below triggers.)
   - **Yes** → continue.
2. **Density-aware read** (per the Density × Steps table above):
   - **Low density** → grep notes/ for the keywords in the current task; only Read paragraphs that match
   - **Medium density** → read `project-context.md` if non-empty; grep `tech-decisions.md` for relevant entries
   - **High density** → full-read both files
3. **Freshness sanity check**: for every file path / function / endpoint mentioned in the loaded notes, do a quick existence check (Glob / `stat` / `grep -l`). Anything missing or moved → flag as `[STALE?]` in thinking; mention to user if it affects current task; offer to update at end of session.
4. **Size budget check**: if the sum of `notes/` files exceeds **1500 lines**, propose consolidation before continuing (see `references/memory-protocol.md` § Size budget).

### First-write rule (lazy initialization)

When the **first concrete piece** of project-local technical context appears in the conversation (deployment URL / API endpoint / naming convention / tech decision), propose:

> "I'd like to record this in `.careful-coder/notes/project-context.md` so I remember it next session. **Should I commit this directory to git?** (private repo → usually yes, makes the team share the memory; open-source repo → usually no, may contain internal URLs / domain names.)"

Store the user's answer in `.careful-coder/config.json` so the question is asked exactly once per project. If the user picks "no commit", add `.careful-coder/` to `.gitignore` automatically.

Only on user agreement do you create the directory + copy templates + write the first entry.

Detailed rules: `references/memory-protocol.md`.

---

## Step 1: Requirements + scope boundary

(Tier behavior in the decision table above.)

**Why**: users speak in flows with implicit requirements. Acting immediately → missed requirements / scope creep. Two lists serve two purposes: **requirements** (input/processing/output + edges) and **scope boundary** (what to change vs. NOT change).

If you discover an out-of-scope problem mid-task, **stop and tell the user** — never expand on your own.

**Setting up rollback before you change anything** (moved here from Step 4):
- Clean repo → ensure `git status` is clean; if not, stash unrelated changes
- Big change → `git checkout -b feature/<descriptor>`
- No git → at minimum `cp file.py file.py.bak` for files you'll modify

Details: `references/anti-hack-patterns.md` § scope creep.

---

## Step 2: Read context + align contracts

(Tier behavior in the decision table.)

When required:
- **Renaming any symbol (any tier)** → Grep the symbol across the codebase first. String-referenced sites (test fixtures, config files, dynamic attribute access, JSON keys) won't show up in static analysis but will break at runtime. This applies even to "private" `_foo` names.
- Modifying any existing file → Read the whole file (or relevant region)
- Changing a function signature → Grep all callers
- Adding a new file → look at neighboring code style first
- **Modifying a frontend call** → check the backend handler signature
- **Modifying a backend API** → reverse-grep all frontend callers

**Contract alignment**: if the project has OpenAPI / TypeScript types / Pydantic schema / GraphQL schema, that's the single source of truth. Change schema first, implementation second.

Details: `references/multilang-contract.md`.

---

## Step 3: Write code + verify APIs + scan for hardcoded values

(Tier behavior in the decision table.)

#### API verification

Any API call you're not 100% certain of, **verify before use**. Bar: "I can recite the official signature including parameter order", not "I think I remember".

Methods (fast → slow):
1. Run a one-liner — Python: `python -c "from X import Y; help(Y)"`; Node: `node -e "console.log(Object.keys(require('Y')))"`; Go: `go doc package.Func`
2. Read the source — `pip show <lib>` / `npm ls <lib>`
3. Fetch official docs — WebFetch
4. Ask the user — for internal / private APIs

**Don't import without confirming installed.** If missing, tell the user the install command — don't write code that bombs on their machine.

#### Hardcoded-value scan

Scan your diff for: hardcoded URLs / IPs / ports / keys / paths / magic values / debug residue / commented-out code / vague TODOs.

Details: `references/anti-hack-patterns.md`.

---

## Step 4: Verify (every tier; depth varies)

(Tier behavior in the decision table.)

**Why**: the gap between "looks correct" and "actually runs" is full of typos, missed edges, and hallucinated APIs.

#### Verification tiers (highest signal first)

| Tier | What | Scope of use |
|---|---|---|
| ★★★ | Run the script / start the service, observe real output | High-density work |
| ★★ | Run unit / integration tests | Medium-density work, when tests exist or you wrote one |
| ★ | Import / lint / type-check | Low-density work, or when end-to-end is impossible |

If you can only reach ★ on a high-density task, explicitly tell the user: "I couldn't test X here because Y. Recommended verification: Z."

#### For high-density tasks: also do these

- **Diff self-review**: read your full `git diff`; flag noise diff (unrelated typos / whitespace / import reorders) → revert or call out separately
- **Check off requirements + scope boundary** (the two lists from Step 1)
- **Rollback path still clean?** (the rollback was set up in Step 1; here you re-confirm it's still usable)

#### Reporting format & forbidden phrasings

Both live in **one place**: `references/self-check-protocol.md` §V (per-tier templates) and §VI (forbidden phrasings blacklist). SKILL.md does not duplicate them.

---

## Difficulty consultation (off by default; proposed when criteria are met)

**Why**: some points are objectively error-prone (concurrency / async / security / complex state machines). Multi-agent debate reduces error rate at a cost; default off; only proposed under strict conditions.

#### Trigger conditions (all three must hold)

- (a) Hits a **hard difficulty** in `references/difficulty-criteria.md` (concurrency / async / IPC / complex regex / security / unfamiliar advanced API / complex state machine)
- (b) On a runtime path (not throwaway)
- (c) Failure impact ≥ one user-visible feature

#### Proposal phrasing (with concrete cost)

> The current task involves [specific concrete reason — e.g., "asyncio task cancellation semantics" — *not* "feels hard"]. Historically high error rate; mistake would affect [specific feature].
>
> Want me to start a **three-way debate**? Spawns 3 sub-agents, each independently analyzes; they then debate to find each other's gaps. I supervise.
>
> **Cost estimate**: 3 sub-agents × 2 rounds ≈ 6× single-agent token cost. For this task that's roughly **[N tokens / $X]** based on the current task length.

Each accepted debate is logged to `.careful-coder/_debate-log.md` (auto-created on first use; sibling to `notes/`, **not** inside it — does not consume the 1500-line notes/ size budget). The user can set a monthly budget (`.careful-coder/config.json`: `debate_budget_per_month`); on hitting the budget, the skill skips the proposal entirely and mentions the skipped opportunity once in the final report.

Full protocol: `references/multi-agent-protocol.md`.

---

## Multi-agent orchestration

**Default**: solo main agent.

Propose parallel agents when:
- Task cleanly decomposes into ≥ 2 independent sub-tasks (e.g., simultaneously checking frontend / backend / tests)
- Task benefits from multiple review angles
- Difficulty consultation triggers (above)

**How to derive each sub-agent's "do NOT touch" boundary**: grep the current task for the smallest set of directories / modules it logically needs, list those as the scope, list everything *else* as do-not-touch (with examples specific to the project, e.g., `do NOT touch: tests/, scripts/, docs/, any module not under src/feature/<this>/`). Don't write open-ended boundaries like "do not touch unrelated code" — that's underspecified.

Details: `references/multi-agent-protocol.md`.

---

## Project memory (lazy + scoped + size-budgeted)

**Boundary with host memory**: the host already handles user preferences and cross-project feedback. notes/ is for **project-local technical facts** only. (If you're unsure: default to letting host memory handle it, not careful-coder.)

#### What goes in notes/

| File | Content |
|---|---|
| `project-context.md` | Deployment URLs / API endpoints / key field names / env config |
| `tech-decisions.md` | Models, algorithms, special techniques (e.g., stdout IPC, pyodide), trade-off-laden tech selections |

#### Size budget

`notes/` total ≤ **1500 lines**. Beyond that, Step 0 forces a consolidation proposal before continuing the task.

#### On-demand consolidation

No automatic line/write thresholds for normal triggering. Consolidation happens when: user asks; main agent detects inconsistency; size budget hit; freshness sanity check found stale entries.

Details: `references/memory-protocol.md`.

---

## Further reading

| File | Content |
|---|---|
| `references/difficulty-criteria.md` | Hard-difficulty checklist + runtime/impact tests |
| `references/self-check-protocol.md` | **Single source of truth** for per-tier reporting + forbidden phrasings + per-language run commands + rollback playbook |
| `references/multi-agent-protocol.md` | Multi-agent orchestration + three-way debate + cost / budget |
| `references/language-discipline.md` | English thinking + density tiers + vague-word & leak-pattern blacklists + per-tier forbidden behaviors |
| `references/multilang-contract.md` | Front↔back contract alignment + cross-language change patterns |
| `references/anti-hack-patterns.md` | Hardcode scan + scope-creep prevention + counterintuitive logic catalog |
| `references/memory-protocol.md` | notes/ lazy init + git-commit opt-in + freshness check + size budget + division of labor with host memory |
| `CHANGELOG.md` | v1 → v2 → v3 → v4 → v5 changes and reasoning |
| `scripts/lint.py` | Runs consistency checks across SKILL.md + references (cross-reference validity, rule duplication, terminology drift) |

---

## Closing

The point of careful-coder is **right effort for the task**. A trivial rename gets a 1-line confirmation; a substantial multi-service change gets the full pipeline. Scale your effort to the density; don't omit steps entirely; admit unknowns; verify before declaring done.

When uncertain → "spend 5 seconds verifying" beats "guess and hope".
When the task is hard → "propose a debate (with cost estimate)" beats "push through alone".
When tempted to be vague → "concrete statement + admit unknowns" beats "I think / probably / should work".
When in doubt about tier → default to **medium**.
