# Self-Check Protocol — Single Source of Truth for Per-Tier Reporting + Forbidden Phrasings

This document is the **single source of truth** for:
- Per-tier reporting templates (§ V)
- Forbidden phrasings blacklist (§ VI)
- Per-language run commands (§ I)
- Rollback playbook (§ IV)

SKILL.md does not duplicate any of these — it links here.

<summary>
Contents:
- § I: per-language ★/★★/★★★ run commands (Python, JS/TS, Go, Rust, frontend) + test-discovery sanity check (0-tests-ran ≠ pass)
- § II: diff self-review (noise-diff catalog, dependency check) — high-density only
- § III: requirements + scope-boundary check-off — high-density only
- § IV: rollback playbook (set up before, re-confirm after; problem-severity table)
- § V: reporting templates by density (LOW 1 line, MEDIUM 3-5 bullets, HIGH full template)
- § VI: forbidden phrasings blacklist (canonical, every density)

Read full when: about to write the report; about to verify; need exact run command for a language; hit a problem during self-check and need the severity-handling table.
Skim sufficient when: already know which tier you reached and don't need a per-language reminder — section headings tell you where the answer is.
</summary>

---

## I. Run verification (★★★ → ★★ → ★)

Pick the highest tier you can reach. **At minimum, hit ★** (import / lint / type-check).

### Python

| Tier | Command | Use |
|---|---|---|
| ★★★ | `python script.py` or `python -m mymodule` | Direct run |
| ★★★ | `uvicorn app:app --reload` / `flask run` | Start service |
| ★★ | `pytest -x tests/` or `pytest tests/test_x.py::test_y -v` | Run tests |
| ★ | `python -c "import mymodule"` | Import check |
| ★ | `ruff check .` or `flake8` | Lint |
| ★ | `mypy mymodule/` | Type check |

### JavaScript / TypeScript

| Tier | Command | Use |
|---|---|---|
| ★★★ | `node script.js` / `npm run dev` / `vite` | Direct run / dev server |
| ★★ | `npm test` / `vitest` / `jest` | Run tests |
| ★ | `node -e "require('./mymodule')"` | Import check |
| ★ | `tsc --noEmit` | Type check (TS) |
| ★ | `eslint .` / `biome check` | Lint |

### Go

| Tier | Command | Use |
|---|---|---|
| ★★★ | `go run ./cmd/myapp` | Direct run |
| ★★ | `go test ./...` | Run tests |
| ★ | `go build ./...` | Compile check |
| ★ | `go vet ./...` | Static check |

### Rust

| Tier | Command | Use |
|---|---|---|
| ★★★ | `cargo run` | Direct run |
| ★★ | `cargo test` | Run tests |
| ★ | `cargo check` | Compile check |
| ★ | `cargo clippy` | Lint |

### Frontend (browser-side)

If the change affects browser rendering:
- ★★★ Start dev server, actually open the page, describe what you saw
- ★★ E2E tests (Playwright / Cypress)
- ★ Run `npm run build` to surface bundling errors

### Test-discovery sanity check (★ and ★★ tiers — applies before "the verify passed")

A common silent failure mode: the verify command runs and exits 0, but **didn't actually exercise anything**. Examples:

- `python -m unittest discover` returns 0 tests because the project uses `pytest`-style functions and `unittest` ignores them
- `pytest tests/` exits 0 because there are no `test_*.py` files in `tests/` (typo in directory name; tests are in `test/`)
- `npm test` exits 0 because `package.json` has no test script defined
- `cargo test` exits 0 because no tests exist in the crate yet
- `go test ./...` exits 0 because all `_test.go` files are excluded by build tags

When you run a verify command:

1. **Check the test count line** of the output (e.g., `5 passed`, `0 tests ran`, `Ran 0 tests in 0.000s`)
2. If the count is **0**, treat ★★ as **failed**, not passed. Mention explicitly in the report: "verify command exited 0 but discovered 0 tests; falling back to ★ tier"
3. Investigate why: wrong test framework? wrong directory? missing dependency? Then either fix or honestly report.

**Never** report "tests pass" when 0 tests ran. The exit code is misleading; the count is the truth.

### Tier × density mapping (cross-reference to SKILL.md decision table)

| Density | Minimum verify tier | Notes |
|---|---|---|
| Low | ★ | One import/lint/type-check command. No full pytest. |
| Medium | ★★ if a test exists or you wrote one; else ★★★ run | If neither possible, ★ + explicit "untested because Y". **0 tests discovered ≠ ★★ passed.** |
| High | ★★★ + diff self-review + requirements check-off + rollback path re-confirm | Skipping any of these on high-density work is a discipline failure |

---

## II. Diff self-review (high-density tasks)

After writing, read your full diff via `git diff` or `git diff --cached`. For each file, answer:

1. **Is every changed line necessary?** Identify "I changed it but it's unrelated to the task". Common noise diffs:
   - Typo fixes (unrelated to task)
   - Whitespace / indentation tweaks
   - Import reordering
   - Comment formatting
   - Quote-style swaps (`'` ↔ `"`)
2. **If you find noise diff:**
   - Related to the task → keep, but call it out separately in the report
   - Unrelated → revert, or split into a separate commit / PR
3. **Check for unnecessary new dependencies:** look at changes to `requirements.txt` / `package.json` / `go.mod`. Any new dependency: explain in the report why it's needed.
4. **Check for hardcode antipatterns** (full list in `anti-hack-patterns.md`).

---

## III. Check off requirements + scope boundary (high-density tasks)

Pull out the two lists from Step 1 and **check them off line by line**.

### Requirements review

For each item:
- [ ] Can you find the corresponding implementation? (Grep keywords to verify)
- [ ] Are edge cases handled? (empty input / file not found / network failure / oversized input)
- [ ] Are error messages clear? (user-friendly vs. internal traceback)

### Scope boundary review

- [ ] Files changed = files listed in Step 1?
- [ ] Did not touch anything Step 1 marked "do not change"?
- [ ] If you did touch something out of scope → **state it explicitly in the report and explain why it was necessary**

---

## IV. Rollback (set up BEFORE; re-confirm AFTER)

The rollback path **is set up before any change** (in Step 1 / Step 2 of SKILL.md), not in Step 4.

### Set up (Step 1 / 2 of SKILL.md)

- Clean repo → ensure `git status` is clean; if not, stash unrelated changes first
- Big change → `git checkout -b feature/<descriptor>`
- No git → `cp file.py file.py.bak` for any file you'll modify

### Re-confirm during Step 4

After self-check, **confirm the rollback path is still usable** (no surprise unrelated changes accumulated; backups not accidentally overwritten; branch hasn't been merged prematurely).

### When self-check finds a problem

| Problem severity | Handling |
|---|---|
| Small (typo / missed edge case) | Fix it, re-run self-check |
| Medium (logic error but local) | Fix, re-run, mention in report |
| Large (overall approach wrong) | `git checkout .` to roll back; redo Step 1 + Step 2; start over |
| Self-check fails ≥ 3 times | Trigger the difficulty-consultation proposal (`multi-agent-protocol.md`) |

---

## V. Reporting templates by density (single source of truth)

SKILL.md links here. **Do not duplicate these elsewhere.**

### Density-to-format mapping

| Density | Format | Length |
|---|---|---|
| **Low** | Single line | 1 line |
| **Medium** | Short bullets | 3-5 bullets |
| **High** | Full template | ~20-40 lines |

### LOW (trivial) — 1 line

```
Renamed `oldName` → `newName` across `auth.py` (3 sites). Import-checked, no errors.
```

That's it. No headers, no sections, no trailing summary.

### MEDIUM (standard) — 3-5 bullets

```
- Added `deactivate_user` to `UserService`, mirrors `activate_user` (sets `deactivated_at = datetime.now()`)
- Raises `UserNotFoundError` via `get_user` delegation, matching the existing convention
- Verified: ran `pytest test_user_service.py` → 2 passed; round-trip activate/deactivate confirmed
- Scope: only touched `user_service.py` + its test file
```

No 5-section template. Brief recap + concrete verification + scope statement.

### HIGH (substantial) — full template

```markdown
## Status

### Requirements
✅ [Req 1] — [actually how it was done + key parameters]
✅ [Req 2] — [actually how it was done]
⚠️ [Req 3] — [partial; reason X; recommend Y]
❌ [Req 4] — [not done; reason X; need decision Y]

### Scope boundary
✅ Changed: [file list]
✅ Did not change: [list from Step 1]
⚠️ Out-of-scope changes: [files + why they were necessary]

### Run verification
- [Command 1] → [result]
- [Command 2] → [result]
- Tier reached: ★★★ / ★★ / ★ (state which)
- Untestable parts: [if any, what + why + how the user can verify]

### Diff self-review
- Lines changed: [+X / -Y]
- Noise diff: [none / found, describe]
- New dependencies: [none / list, explain why]
- Hardcode scan: passed / found X, fixed

### Rollback safety (re-confirm)
- Set up at Step 1 as: [feature/xxx / file.py.bak]
- Still usable? [yes / no, why]
- Rollback command: [git checkout main / cp file.py.bak file.py]
```

---

## VI. Forbidden phrasings (single source of truth, every density)

Don't write these in the report — at any density:

- ❌ "Should be fine" / "应该没问题"
- ❌ "Code looks correct" / "看起来对"
- ❌ "Might need testing" / "可能需要测试"
- ❌ "Mostly done" / "基本完成"
- ❌ "Should run in theory" / "理论上能跑"
- ❌ "I haven't tried it but it should be OK" / "我没试过但应该 OK"
- ❌ "It's done." (with no verification statement attached)

If you catch yourself wanting to write any of these → the verify step wasn't done. **Go back and complete it.**

(Note: this section is the only canonical copy. SKILL.md links here; do not duplicate.)
