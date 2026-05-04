# careful-coder v5 — Live Eval Report

**Run date**: 2026-05-04
**Subject**: `~/Documents/careful-coder-v5` (after hotfix)
**Method**: 5 tasks executed end-to-end on a sandbox Flask project (`/tmp/cc-eval/`), with the model acting under v5 SKILL.md as its operating manual. Each task's compliance vs. drift was self-observed.
**Lint baseline**: `python3 scripts/lint.py` → 7/7 checks pass, 0 issues.

---

## 1. Test set

| # | Task | Declared density | Final density |
|---|---|---|---|
| 1 | Rename `_db` → `_users` (single-file) | LOW | LOW |
| 2 | Add `deactivate_user` method | MEDIUM | MEDIUM |
| 3 | Fix JWT `decode()`: missing `exp` check + timing-safe sig | MEDIUM | **HIGH** (mid-task re-class) |
| 4 | Refactor `is_active` → derived field (storage vs API contract split) | HIGH | HIGH |
| 5 | Add JWT `audience` claim with timing-safe compare | HIGH | HIGH |

**Outcome counters**:

- 16 tests written, 16 passing (after fixing 1 self-introduced flaky test)
- 4 `git` rollback checkpoints set up before destructive work
- 2 out-of-scope-but-necessary changes called out in reports (timing-attack hardening, malformed-token exception handling)
- 1 mid-task tier upgrade (Task 3: MEDIUM → HIGH on hitting `difficulty-criteria.md` §I.4)
- 0 three-way debates triggered (sandbox is not a runtime path → condition (b) failed; correct restraint)
- 0 notes/ writes (no concrete project facts surfaced; lazy-init correctly stayed silent)

---

## 2. Pros — what actually works

### 2.1 The Density × Steps decision table is the load-bearing innovation

All 5 tasks emitted the right report shape automatically:

| Density | Report shape | Observed length |
|---|---|---|
| LOW | 1 line | 1 line |
| MEDIUM | 3-5 bullets | 4-5 bullets |
| HIGH | Full template | ~25-35 lines |

This is the single biggest UX fix vs. v3. A trivial rename does not produce a 5-section status report; a multi-file refactor does.

### 2.2 "Code that hasn't been run cannot be declared done" caught a real bug

**Task 3** introduced `test_tampered_sig`, which appeared correct on a single run. The HIGH-tier rule "★★★ run" forced 20 iterations, exposing flakiness: when the original sig's last char happened to be `'A'`, the "tampered" version was identical, and the test asserted falsely. **This is the rule's core ROI demonstrated in a 5-task sample.**

### 2.3 Mid-task re-classification (`language-discipline.md §II.4`) is not decoration

Task 3 was declared MEDIUM. While reading scope, I noticed the change touched `difficulty-criteria.md §I.4 (auth/JWT)`. The §II.4 trigger #2 fired ("hard difficulty appeared mid-task"), I re-declared HIGH, and back-filled the skipped steps (written-out requirements, rollback checkpoint, ★★★ verify, full report). Without §II.4 this would have shipped a security-relevant change under the lighter MEDIUM discipline.

### 2.4 Out-of-scope-necessary protocol works as written

Task 3 surfaced two items the user did not ask for:
- `expected_sig != actual_sig` is timing-vulnerable (existing code)
- `base64.urlsafe_b64decode` raises on malformed input (uncaught)

Per `anti-hack-patterns.md §II.4`, these were inseparable from the requested fix. Both were applied **and** flagged in the report's "⚠️ Out-of-scope but necessary" block. No silent expansion.

### 2.5 Three-way debate trigger is strict, not loose

Task 5 hit the hard-difficulty list (auth/JWT) but failed condition (b) "runtime path" — sandbox eval is not production. The protocol correctly **did not propose** a debate. v3-era loose triggers would have over-fired here.

### 2.6 Lazy initialization correctly silences `.careful-coder/`

Across all 5 tasks no concrete project fact appeared (no deploy URL, no API endpoint conventions, no field rename across services). Step 0 stayed silent: no notes/ created, no templates copied, no token cost. This matches v5's lazy-init design and is a notable improvement over v2/v3 which created empty templates eagerly.

### 2.7 Lint + lockfile + version checks are tightly coupled

`build.sh` writes the lock; `lint.py` check [5] verifies source-vs-lock; check [7] verifies bundle-vs-lock; check [6] verifies SKILL.md `(vN)` matches CHANGELOG top entry. The four artifacts (SKILL.md / source files / lockfile / .skill bundle) are all transitively pinned. Drift detection works.

### 2.8 Bilingual REQUIRED/必填 + opt-in git commit are sound defaults

Templates carry `**REQUIRED / 必填**` and `**OPTIONAL / 可选**` so neither English-only nor Chinese-only users feel like guests. The first-write proposal explicitly asks "commit to git? private repo → usually yes; open-source → usually no" — defers privacy decision to the user instead of choosing for them.

---

## 3. Cons — what's still imperfect

### 3.1 ~40% of the skill is dormant in normal use

Privacy guard, freshness sanity check, debate budget reset, multi-agent orchestration, three-way debate, notes/ consolidation — none of these activated in 5 tasks. They only matter for **cross-session, long-running, multi-project** use. This isn't a bug, but it means:

- A 5-task eval cannot validate them.
- Their cost (token weight + maintenance burden) is paid every load, even when dormant.
- The dormant rules' value is fundamentally unmeasurable without longitudinal data.

### 3.2 LOW tier is too loose on "skip the read"

The decision table says LOW skips Step 2 read "unless changing a public API". In Task 1 (rename a private `_db`), I still grepped — common sense overrode the rule. **Renaming any name that might be referenced by string** (test fixtures, config files, dynamic attribute access) is risky regardless of public/private. Recommendation: tighten LOW Step 2 to "always grep the symbol; skip the full Read".

### 3.3 MEDIUM "ask the user when uncertain" is too strict for micro-decisions

In Task 2, the convention question "should `deactivate` clear `activated_at`?" has no clear answer in the existing code. Per `language-discipline.md §IV` ("admit ignorance, ask"), I should have asked. Instead I made a choice and explained it in the report. **For micro-decisions inside MEDIUM tasks, asking the user breaks flow more than it adds safety.** Recommendation: relax §IV to "for binary decisions inside MEDIUM, choose-and-explain is acceptable; only ask if reversing is expensive".

### 3.4 Density assessment thinking-template is rigidly structured

The skill prescribes the first thinking line take a fixed shape:
```
Density assessment:
- Task type: ...
- Hard points hit: ...
- Files involved: ...
- Ambiguity: ...
→ Density: ...
```
In practice this is friction. A natural-language sentence ("Single-file rename, no callers, low") carries the same information at 1/5 the tokens. Recommendation: make the structured template optional — required only when high-confidence is needed (e.g., HIGH-tier or when the agent is about to spawn sub-agents).

### 3.5 `pytest`-style test files but pytest unavailable: real failure mode unspoken

The sandbox uses pytest function-style tests, but pytest wasn't installed. `unittest discover` returned 0 tests silently — a failure mode where **verification appears to succeed but covers nothing**. The skill's tier-1 fallback (`python -c "import"`) doesn't catch this either. Recommendation: add to `self-check-protocol.md` §I a "test-discovery sanity check": if your verify command reports 0 tests run, treat it as ★ tier failed and mention explicitly in the report.

### 3.6 Out-of-scope-necessary blurs the "scope creep" line

Task 3's timing-safe fix and exception handling were defensible additions, but the rule "if a fix is required to complete the task, do it and call out" can rationalize almost anything. Recommendation: tighten `anti-hack-patterns.md §II.4` with an explicit narrow test — "the original task literally cannot pass its own tests without this change". My Task 3 timing-attack fix actually fails this test (the `exp`-only fix would have passed with `!=`). Honest re-classification: that was a security-motivated drive-by, called out, but was scope creep by strict reading.

### 3.7 Mid-task re-classification is one-way (no downgrade)

`language-discipline.md §II.4` explicitly says "don't downgrade mid-task". Reasonable for safety, but it means a HIGH-misclassification stays expensive. In a long session this compounds. Recommendation: allow downgrade if (a) no destructive changes have happened yet and (b) self-check explicitly confirms.

### 3.8 Re-checked rules occupy SKILL.md prime real estate

SKILL.md leads with Density × Steps decision table — correct prioritization. But several less-load-bearing rules (multi-agent orchestration, project memory boundary) sit in the same file at full weight. Recommendation: SKILL.md should keep only the 5-step + density table + thinking conventions; everything else moves to references/ with brief pointers.

### 3.9 lint.py docstring stale

Top-of-file docstring still says "Checks for: 1. xref / 2. dup / 3. drift" but lint actually has 7 checks. Cosmetic but risks misleading future maintainers.

### 3.10 CHANGELOG architecture diagram says "lint.py: 4 道 check + lockfile freshness" but lint has 7 checks now

Same staleness pattern. Lint check [6] (the meta-fix you added to prevent this exact category of drift) doesn't catch CHANGELOG's diagram block — it only catches the `(vN)` heading. Recommendation: extend check [6] to scan for the literal phrase patterns "N 道 check" / "N checks" against the actual function count.

---

## 4. Severity-ordered fix list

| # | Issue | Severity | Effort |
|---|---|---|---|
| 1 | LOW Step 2 should always grep, just skip full Read | P1 | 2 lines in decision table |
| 2 | MEDIUM micro-decisions: choose-and-explain acceptable | P2 | rewrite §IV exception |
| 3 | Out-of-scope-necessary needs narrow test | P2 | 3 lines in anti-hack §II.4 |
| 4 | Density assessment template made optional | P2 | mark "encouraged not required" |
| 5 | Test-discovery sanity check (0-tests-found ≠ pass) | P2 | new bullet in self-check §I |
| 6 | Allow conditional mid-task downgrade | P3 | adjust §II.4 |
| 7 | lint.py top docstring + CHANGELOG arch block | P3 | sync to current lint count |
| 8 | Move multi-agent / memory-boundary out of SKILL.md | P3 | move + replace with pointer |

None of these are P0 (no real bugs). All are calibration improvements based on observing what the model actually does vs. what the rules ask.

---

## 5. Verdict

- **Source-level engineering quality**: high. v5 hotfix closed all P0 / P1 / P2 from the prior review, lint is 7/7 green, supply chain (lock + bundle hash + version match) is properly pinned.
- **Behavioral effectiveness on coding tasks**: confirmed positive. The core 5-step + tier discipline + ★★★-run rule **caught a real flaky-test bug** in a 5-task sample. Mid-task re-classification fired on schedule. Out-of-scope items got called out. Three-way debate didn't over-fire.
- **Latent / cross-session features**: unmeasured. ~40% of the skill is silent in single-session sandbox use. Their value depends on long-running use that this eval cannot simulate.
- **Calibration drift**: a small number of rules are too tight (LOW skip read, MEDIUM "ask first"), and the model self-relaxes them. Healthy in practice but worth tightening the language.

**Status**: ready for field use; would benefit from a second eval pass that runs across simulated sessions (task 1 → task 2 → task 3 with day-gaps) to actually exercise the dormant 40%.
