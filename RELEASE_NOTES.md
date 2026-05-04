# v5.1-beta — 2026-05-05 (Pre-release)

> ⚠️ **Beta release.** ~40% of features (cross-session memory, debate-budget reset, freshness check, consolidation, multi-agent) require longitudinal validation that single-session sandbox cannot provide. API surface and config schema may change before v5.0 stable.

## What's new in v5.1-beta

A **cost-reduction + release-prep** sub-release. No semantic changes to the discipline; structural reorganization to lower per-invocation token cost and harden the release pipeline.

- **SKILL.md slimmed −38%** (4634 → 2893 tokens) — moved marketing/intro to `README.md`, compressed Step prose, kept the Density × Steps decision table verbatim. Hot-path cost drops accordingly (~4700 → ~2900 tokens uncached LOW; ~700 tokens with 80% cache hit).
- **Reference summary blocks** — each `references/*.md` now begins with a `<summary>` listing its sections so Claude can skim before deep-reading.
- **lint check `[8] SKILL.md size guard`** — soft-warn at 2700 tokens, hard cap at 3000. Prevents future hot-path bloat at PR time.
- **lint check `[9] README check-count consistency`** — self-referential drift catcher: the README's "N consistency checks" paragraph stays in sync with `lint.py`.
- **lint check `[10] RELEASE_NOTES version match`** — RELEASE_NOTES.md first H1 must declare the same version as `SKILL.md` and `CHANGELOG.md` top entry. Prevents the v5.0→v5.1 release-body drift that triggered this hotfix.
- **`lint.py --strict`** — promotes lockfile drift / bundle drift / size-guard warnings to hard errors. Required for CI / before release; default mode stays lenient for fresh clones.
- **Reproducible release pipeline** — `scripts/release.sh v<tag>` runs strict lint, rebuilds the bundle, tags, pushes, creates the GitHub release with bundle attached. Auto-detects pre-release from `-suffix`. Dry-run flag for predeployment. CI fallback at `.github/workflows/release.yml` for tag-only release.
- **`<!-- CACHE BOUNDARY -->` marker** at the end of `SKILL.md` — documents that SKILL.md content is static and cacheable; project-level injections (notes/) belong in user messages.

## Carried forward from v5.0-beta

- Density-aware engineering discipline (LOW / MEDIUM / HIGH) so trivial edits stay light and substantial work gets the full rollback + verify + report treatment.
- Anti-hallucination API verification (`python -c "help(X)"`, `node -e`, official docs lookup before using uncertain APIs).
- Rename-safe scope discipline — every rename greps the symbol across the codebase, including string-referenced sites in test fixtures and configs.
- Scope-creep prevention — out-of-scope fixes are *suggested*, not silently applied. Inseparable-dependency exception requires the original task's tests to fail without the change.
- Privacy guard — emails, tokens, IPs, long key-like strings are auto-redacted before being written to project notes.
- Cross-session memory at `.careful-coder/notes/` — deployment URLs, API endpoints, field naming conventions persist across chats.
- Forbidden-phrasings + leak-pattern blacklist — no "should be fine" / "应该没问题" / "Let me check…" residue.
- Reproducible build (`scripts/build.sh`) + lint (`scripts/lint.py`) + `careful-coder.lock` with source and bundle hashes.

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
git clone --branch v5.1-beta https://github.com/Ice-teapop/careful-coder.git
# Drop into ~/.claude/skills/careful-coder/ (or your host's equivalent)
```

### Verify

After installation, ask Claude Code to make a code change. The skill should activate automatically — you'll see density classification (LOW / MEDIUM / HIGH) in the response.

## Roadmap to v5.0-stable

1. ✅ v5.0-beta — first public Beta.
2. ✅ v5.1-beta — cost-reduction + release-pipeline hardening (this release).
3. ⏳ 1–2 weeks of [L] longitudinal eval covering cross-session, freshness, budget reset.
4. ⏳ Add 5–7 cross-session tests to `evals/TEST_PLAN.md`.
5. ⏳ v5.2-beta — replace LLM-token work with deterministic scripts (`freshness-check.py`, `diff-noise-detector.py`, `notes-size-check.py`).
6. ⏳ Promote → `v5.0` stable when A/B clear-value rate hits ≥ 60% per `evals/TEST_PLAN.md` § 19.

## Feedback

This is a Beta. Bug reports, behavioral observations, and "this rule never fires for me" are all valuable. Use the issue templates:

- `[bug]` — skill misfired, fired when it shouldn't, or produced wrong output.
- `[beta-feedback]` — observations from real use, frequency notes, suggestions.

## Full changelog

See [`CHANGELOG.md`](CHANGELOG.md) for the complete v1 → v5.1-beta history.
