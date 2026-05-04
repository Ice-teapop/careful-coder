# Project Memory Protocol — Lazy Init, Density-Aware, Size-Budgeted (v5)

This document defines `.careful-coder/` maintenance: what it's for, what it's *not* for (vs. host memory), how to lazy-init it, how to load it density-aware, how to keep it fresh, and how to keep it bounded.

---

## I. Division of labor with host memory

The host (Claude Code / Cowork / Claude.ai) typically already has its own memory system that handles **user preferences and cross-project / cross-session feedback**. `careful-coder` notes/ does **not** duplicate that. Notes/ is for **project-local technical facts** that the host's memory is poorly shaped for.

### What goes in `careful-coder` notes/

- Deployment URLs (dev / staging / prod)
- API endpoints + payload conventions
- Database / table / column / field naming
- Project-specific environment variables
- Tech selections specific to this project
- Project-specific gotchas

### What does **not** go in `careful-coder` notes/

- User personal preferences (host handles)
- Cross-project work style (host handles)
- General code style preferences not tied to *this* project (host handles)
- Conversation history / chat archive
- Anything not strongly grounded in a specific file / endpoint / field

### Decision rule

Before writing anything, ask: **does this fact apply only to this project, or generally to the user across projects?**
- Project-only → notes/
- User-level / cross-project → host memory
- If ambiguous → default to host, keep notes/ minimal

---

## II. Location

```
<project-root>/
└── .careful-coder/
    ├── config.json              (created on first init; stores schema version, git-commit choice, debate budget)
    ├── _debate-log.md           (auto-created on first three-way debate; OUTSIDE notes/, NOT counted toward size budget)
    └── notes/
        ├── project-context.md   (deployment / API / fields / env)
        ├── tech-decisions.md    (model / algo / special techniques)
        └── _archive/            (post-consolidation backups; created on first consolidation)
```

**Path note**: `_debate-log.md` lives at `.careful-coder/_debate-log.md` (sibling to `notes/`), not inside `notes/`. The size budget (§ VIII) applies only to `notes/` — debate-log can grow with usage without consuming the budget.

### Git commit: opt-in (asked once on first init)

Whether to commit `.careful-coder/` to git is asked once on first creation. The choice is stored in `config.json` and never re-asked.

If the user picks "no commit", the skill writes `.careful-coder/` into the project's `.gitignore` automatically.

---

## III. Lazy initialization

Don't auto-create `.careful-coder/` on first encounter. Wait for the **first concrete piece** of project-local technical context.

### What counts as "concrete" (precise list)

The first-write rule fires only when one of these appears in the conversation:

- A specific URL (deployment / API / external service)
- A specific endpoint path (`/api/v1/users`, etc.)
- A specific field name / column name / table name
- A specific environment variable name
- A specific DB host / port / database name
- A specific model name (`gpt-4o`, `claude-sonnet-4`, etc.)
- A specific library + version pin
- A specific framework version pin
- A specific tech selection with a comparison (e.g., "we chose Postgres over MySQL because…")

Generic statements ("this is a Python project", "we use REST APIs") do **not** trigger first-write.

### First-write flow

1. The first concrete item appears.
2. Propose:
   > "I'd like to record this in `.careful-coder/notes/project-context.md` so I remember it next session. **Should I commit `.careful-coder/` to git?** (Private repo → usually yes; open-source → usually no, may contain internal URLs.)"
3. On user agreement:
   - Create `.careful-coder/`, `notes/`
   - Write `config.json`:
     ```json
     {
       "version": 1,
       "commit_to_git": <user_choice>,
       "debate_budget_per_month": null,
       "debates_used_this_month": 0,
       "last_reset_month": "2026-05"
     }
     ```
   - If `commit_to_git: false`, append `.careful-coder/` to `.gitignore`
   - Copy the relevant template from `assets/notes-templates/`
   - Write the first entry; remove the template's `[Example — auto-remove on first real entry]` placeholder

### config.json schema versioning

`version: 1` is the v5 schema. Future skill versions that change schema MUST migrate from older versions, not silently break.

---

## IV. Step 0 loading flow (density-aware)

```
0. Does .careful-coder/notes/ exist?
   - No → carry on (don't initialize unsolicited)
   - Yes → continue
1. Determine task density (low / medium / high) — see SKILL.md decision table
2. Reset debate budget if needed (defensive — handles malformed / partial / future-version `config.json`):
   - Try to read `config.json`
   - If file is missing, unparseable JSON, or any required field is absent → treat as needing init:
     → set `last_reset_month` to current month
     → set `debates_used_this_month = 0`
     → preserve any unknown future fields you don't recognize (forward-compat)
     → write `config.json` back
   - Otherwise (file is valid):
     → if current month > `config.last_reset_month`:
       → set `debates_used_this_month = 0`
       → set `last_reset_month` to current month
       → write `config.json` back
3. Load notes by density:
   - LOW    → grep notes/ for keywords from the current task; only Read paragraphs that match
   - MEDIUM → Read project-context.md if non-empty; grep tech-decisions.md for relevant entries
   - HIGH   → full-Read both project-context.md and tech-decisions.md
4. Freshness sanity check (density-aware — see § V)
5. Size budget check (see § VIII)
6. Proceed to Step 1
```

The "size > template baseline" check (skip empty templates) still applies — don't waste tokens reading files that just contain placeholder structure.

---

## V. Freshness sanity check (density-aware)

Freshness check scope scales with density:

| Density | Freshness scope |
|---|---|
| **LOW** | None — at low density we only grepped a few sections; doing a full Glob/stat sweep would dominate the cost. |
| **MEDIUM** | Only the references found in the paragraphs you actually read or grepped. |
| **HIGH** | Full check: every concrete file path / function / endpoint mentioned in the loaded content. |

For each reference checked, do a quick existence check (Glob / `stat` / `grep -l`).

Anything missing or moved → mark in thinking as `[STALE? notes mention X but not in codebase]`. If the staleness affects the current task, flag to user immediately:

> "Your project-context.md mentions endpoint `/api/v1/users` but I don't see it in the routes anymore — is it still around?"

If staleness doesn't affect current task, defer to end-of-session and propose consolidation.

---

## VI. Write triggers

### project-context.md / tech-decisions.md

Triggers as before (see § III "concrete" list).

### Notify on every write

> "I've recorded [X] in notes/[file].md."

### Privacy guard (every write)

#### What we automatically redact (regex-based)

Before writing, scan and redact:
- Email addresses → `<redacted-email>`
- Phone numbers → `<redacted-phone>`
- Long alphanumeric tokens / API keys / secrets (≥ 20 chars looking key-like) → `<redacted-secret>`
- Real public IP addresses → `<redacted-ip>` (unless they're documented service IPs)

#### What we do NOT catch automatically (must be self-checked)

These leak categories are **not** caught by regex; the main agent must self-check before writing verbatim content:

- **Internal project codenames** — e.g., "Project Aurora", "the Phoenix migration"
- **Customer / company names** — e.g., specific paying-customer references
- **Colleague names** — first-name + role references ("told me to ask the SRE team's John")
- **Internal domain naming patterns** — `*.internal.*`, `*.corp.*`, `*.example.com`, internal subdomain conventions
- **Slack channel names** — `#auth-team`, `#incident-2026-Q2`
- **Jira / Linear / GitHub ticket id patterns specific to your org** — if your project uses a unique prefix, the IDs leak the project name
- **Internal tool names** — proprietary tools the user mentions casually ("we use FooBar to deploy")
- **Internal architecture leaks** — e.g., "the legacy ORM we're trying to kill"

Before writing verbatim user content into notes/, scan the entry for these categories. If unsure → ask the user before writing.

---

## VII. On-demand consolidation

No automatic line/write thresholds. Consolidation when:

1. User explicitly asks
2. Main agent detects inconsistency
3. Size budget hit (§ VIII)
4. Freshness check found stale entries

### Flow

1. Tell user what triggered + what changes
2. Backup → `.careful-coder/notes/_archive/<YYYY-MM-DD>/`
3. Consolidate (merge dups, drop stale with per-entry confirmation)
4. Report; allow rollback from `_archive/`

---

## VIII. Size budget (notes/ ≤ 1500 lines of *content*)

Notes/ files combined should not exceed **1500 lines of content**. The cap excludes:

- Empty table rows (header + separator only, no data)
- `---` separator lines
- Lines containing only `(Auto-appended by careful-coder, most recent first)` or similar placeholders
- Lines containing only `[Example — auto-remove on first real entry]` markers
- Comment lines starting with `>` blockquote prefixes (since they're meta, not content)

**Why exclude skeleton**: a fresh `project-context.md` template is ~99 lines with empty tables and section markers. Counting these toward 1500 lines means the budget is half-eaten before any real content lands.

### When budget hit

1. Step 0 stops normal loading and proposes consolidation
2. User can choose: consolidate now / temporarily proceed / increase the budget in `config.json`
3. After consolidation, normal loading resumes

---

## IX. Cross-session continuity

`notes/` is project's "long-term memory" if committed; otherwise per-developer.

When notes/ disagrees with current code:
1. Flag in thinking
2. Ask user
3. Update notes/ or code so they agree

**Never silently continue when notes/ disagrees with reality.**

---

## X. Required template fields (quick reference)

Templates live in `assets/notes-templates/`. Each section is marked **REQUIRED / 必填** or **OPTIONAL / 可选** (bilingual labels for clarity).

The skill copies the template on first init; the first real entry triggers automatic removal of the `[Example — auto-remove on first real entry]` placeholder block.

Detailed templates: `assets/notes-templates/`.
