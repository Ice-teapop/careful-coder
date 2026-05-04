# careful-coder

A Claude Code skill that enforces a tier-aware engineering discipline to systematically prevent the most common AI coding failures.

**Status: v5.0-beta** (released 2026-05-04). See [Known limitations](#known-limitations) below.

---

## What it does

`careful-coder` activates whenever you ask Claude Code to write, modify, debug, or refactor code. It enforces:

- **Density-aware steps** — trivial edits stay light (1-line report, no over-engineering); substantial work gets the full discipline (rollback, contract alignment, ★★★ verify, full template)
- **Anti-hallucination API verification** — uncertain APIs get verified before use (`python -c "help(X)"`, `node -e`, official docs)
- **Rename-safe scope discipline** — every rename greps the symbol across the codebase (string-referenced sites in test fixtures, configs, dynamic attribute access)
- **Scope-creep prevention** — out-of-scope fixes get *suggested*, not silently applied
- **Privacy guard** — emails, tokens, IPs are auto-redacted before being written to project notes
- **Cross-session memory** — deployment URLs, API endpoints, field naming conventions stick across chats via `.careful-coder/notes/`
- **Forbidden phrasings + leak-pattern blacklist** — no "should be fine" / "应该没问题" / "Let me check…" residue

---

## Why this skill exists

LLMs systematically fail at writing code in these ways:

- **API hallucination**: inventing function names / parameters / libraries
- **Skipping context**: editing unfamiliar code without reading it
- **Claiming code works without running it**
- **Declaring done while requirements remain unmet**
- **Scope creep**: user asked for A, you "also fixed" B, C, D
- **Hardcoding shortcuts**: secrets/paths/magic numbers baked in
- **Cross-turn amnesia**: forgetting deployment URLs / API endpoints discussed earlier

`careful-coder` addresses these with a tier-aware discipline + thinking-flow conventions + per-project memory. *Right effort for the task* is the principle.

---

## Installation

### Option A: as a Claude Code skill bundle

```bash
# 1. Build the .skill bundle (regenerates lockfile + bundle hash)
cd careful-coder-v5
./scripts/build.sh

# 2. The bundle is written to careful-coder-v5.skill
# Install it via your Claude Code skills directory (per your host's instructions)
```

### Option B: direct source install

Drop the `careful-coder-v5/` directory into your Claude Code skills location (typically `~/.claude/skills/careful-coder/`). The skill will auto-load when Claude Code reads its frontmatter.

### Verify

After installation, ask Claude Code to make a code change. The skill should activate automatically — you'll see density classification ("LOW / MEDIUM / HIGH") in the response.

---

## Quick start

You don't invoke it manually. The skill triggers on natural coding requests:

| You say | Density | What happens |
|---|---|---|
| "rename `_db` to `_users` in service.py" | LOW | greps the symbol, edits, runs `python -c "import service"`, 1-line report |
| "fix the bug in `average([])` — it crashes" | MEDIUM | reads context, picks behavior with explanation, adds a test, runs it, 3-5 bullet report |
| "rename `created_at` → `created` across the project" | HIGH | sets up `git checkout -b` rollback, greps all callers, updates in order, runs full test suite, full template report |

The first time you mention a deployment URL or API endpoint, the skill proposes:

> "I'd like to record this in `.careful-coder/notes/project-context.md`. Should I commit `.careful-coder/` to git? (Private repo → usually yes, makes the team share; open-source → usually no, may contain internal URLs.)"

Your answer is stored in `.careful-coder/config.json` and never re-asked for this project.

---

## Architecture

```
careful-coder-v5/
├── SKILL.md                    # main entry — density × steps decision table
├── CHANGELOG.md                # v1 → v5.0-beta history
├── README.md                   # this file
├── LICENSE                     # MIT
├── careful-coder.lock          # source + bundle sha256 hashes
├── careful-coder-v5.skill      # packaged bundle (build.sh output)
├── references/                 # 7 deep-dive docs
│   ├── difficulty-criteria.md
│   ├── self-check-protocol.md
│   ├── multi-agent-protocol.md
│   ├── language-discipline.md
│   ├── multilang-contract.md
│   ├── anti-hack-patterns.md
│   └── memory-protocol.md
├── assets/notes-templates/     # bilingual REQUIRED/必填 templates
└── scripts/
    ├── lint.py                 # 7 consistency checks
    └── build.sh                # reproducible bundle build
```

`SKILL.md` is the only file Claude Code loads at every invocation. References are read on demand.

---

## Known limitations

This Beta release is honest about what it has and hasn't proven:

### Validated in single-session A/B sandbox (60% of features)

The 5-step discipline + density tiers + rename grep + scope-creep prevention + verify protocol — all empirically tested via 20-test A/B run. Arm A: 20/20 PASS, 0 real defects. Arm B (vanilla): 5 real defects across 11 failures.

### Not yet validated longitudinally (40% of features)

- **Cross-session notes/ value** — deployment URLs / API endpoints / field conventions persisting across days
- **Freshness sanity check** — flagging stale references when code moves
- **Debate budget monthly reset** — `config.json` schema designed for it, but month-rollover behavior needs real time-gap testing
- **Notes/ consolidation at 1500-line size budget** — designed but never triggered in single-session tests
- **Three-way debate end-to-end** — strict trigger correctly *did not fire* in sandbox (correct restraint), but accepted-debate flow is unexercised

These features are architected and unit-coherent; their real-world value will be measured during the Beta period.

### Other caveats

- **Privacy guard is regex-based.** Catches emails / phones / long key-like strings / IPs. Does NOT catch project codenames, customer names, internal domain conventions, Slack channels, Jira IDs (documented in `references/memory-protocol.md` § VI).
- **Three-way debate cost.** ~6× single-agent token. Default monthly budget is `null` (unlimited) — set `debate_budget_per_month` in `.careful-coder/config.json` to cap.
- **Project-language detection is "first observation wins"** — switches thinking to project's language on first non-English identifier or comment. Edge cases exist for mixed codebases.

---

## Development

### Run the lint suite

```bash
python3 scripts/lint.py
```

7 checks: cross-reference validity, forbidden-phrasings single source, reporting template single source, tier terminology consistency, lockfile freshness, version label consistency, .skill bundle hash drift.

### Rebuild the bundle

```bash
./scripts/build.sh                        # rebuild in place
./scripts/build.sh /path/to/output        # write bundle elsewhere
SKILL_PACKAGER=/path/to/package_skill.py \
  ./scripts/build.sh                      # use a non-default packager location
```

### Roadmap to v5.0-stable

1. ✅ Beta release (this milestone)
2. ⏳ 1-2 weeks of [L] longitudinal eval (cross-session, freshness, budget reset)
3. ⏳ Add 5-7 cross-session tests to `evals/TEST_PLAN.md`
4. ⏳ Promote v5.0-beta → v5.0-stable when A/B clear-value rate hits ≥ 60% per `evals/TEST_PLAN.md` § 19

---

## Feedback

This is a Beta. Bug reports, behavioral observations, and "this rule never fires for me" are all valuable. Open an issue or contact the maintainer.

---

## License

MIT — see `LICENSE`.
