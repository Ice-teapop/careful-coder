# v5.0-beta — 2026-05-04 (Pre-release)

> ⚠️ **Beta release.** ~40% of features (cross-session memory, debate-budget reset, freshness check, consolidation, multi-agent) require longitudinal validation that single-session sandbox cannot provide. API surface and config schema may change before v5.0 stable.

## What's new in this release

This is the first public release of `careful-coder` v5. It bundles:

- A density-aware engineering discipline (LOW / MEDIUM / HIGH) so trivial edits stay light and substantial work gets the full rollback + verify + report treatment.
- Anti-hallucination API verification (`python -c "help(X)"`, `node -e`, official docs lookup before using uncertain APIs).
- Rename-safe scope discipline — every rename greps the symbol across the codebase, including string-referenced sites in test fixtures and configs.
- Scope-creep prevention — out-of-scope fixes are *suggested*, not silently applied.
- Privacy guard — emails, tokens, IPs, long key-like strings are auto-redacted before being written to project notes.
- Cross-session memory at `.careful-coder/notes/` — deployment URLs, API endpoints, field naming conventions persist across chats.
- Forbidden-phrasings + leak-pattern blacklist — no "should be fine" / "应该没问题" / "Let me check…" residue.
- Reproducible build (`scripts/build.sh`) + 7-check lint (`scripts/lint.py`) + `careful-coder.lock` with source and bundle hashes.

## Validated vs. not yet validated

**Validated in single-session A/B sandbox** (60% of features) — 5-step discipline, density tiers, rename grep, scope-creep prevention, verify protocol. 20-test A/B run: arm A 20/20 PASS with 0 real defects; vanilla arm 5 real defects across 11 failures.

**Not yet validated longitudinally** (40% of features) — cross-session notes value, freshness sanity check, debate budget monthly reset, notes/ consolidation at 1500-line size budget, three-way debate end-to-end. These are architected and unit-coherent; their real-world value will be measured during the Beta period.

See `README.md` § Known limitations for the full rundown of caveats (privacy guard regex coverage, debate token cost, project-language detection edge cases).

## Install

### Option A — Skill bundle

1. Download `careful-coder-v5.skill` from the Assets section below.
2. Install it into your Claude Code skills directory per your host's instructions.

### Option B — Source

```bash
git clone --branch v5.0-beta https://github.com/<your-username>/careful-coder.git
# Drop into ~/.claude/skills/careful-coder/ (or your host's equivalent)
```

### Verify

After installation, ask Claude Code to make a code change. The skill should activate automatically — you'll see density classification (LOW / MEDIUM / HIGH) in the response.

## Roadmap to v5.0-stable

1. Beta release (this milestone).
2. 1–2 weeks of [L] longitudinal eval covering cross-session, freshness, budget reset.
3. Add 5–7 cross-session tests to `evals/TEST_PLAN.md`.
4. Promote v5.0-beta → v5.0-stable when A/B clear-value rate hits ≥ 60% per `evals/TEST_PLAN.md` § 19.

## Feedback

This is a Beta. Bug reports, behavioral observations, and "this rule never fires for me" are all valuable. Use the issue templates:

- `[bug]` — skill misfired, fired when it shouldn't, or produced wrong output.
- `[beta-feedback]` — observations from real use, frequency notes, suggestions.

## Full changelog

See [`CHANGELOG.md`](CHANGELOG.md) for the complete v1 → v5.0-beta history.
