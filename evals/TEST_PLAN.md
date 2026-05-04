# careful-coder v5 — Comprehensive A/B Test Plan

**Purpose**: Verify the **40% dormant features** (cross-session memory, privacy guard, freshness check, debate budget, consolidation, multi-agent) that single-session sandbox eval cannot exercise. Plus regression-test the active 60% in real-world conditions.

**Method**: For each test, run **twice** — once with the skill loaded, once without (or with a stripped baseline) — and compare. Some tests are longitudinal (must span multiple sessions / days); these are marked **[L]**.

---

## How to use this document

1. **Pre-flight** (§ 0) once per machine
2. Pick a test by ID (e.g., `T-CORE-01`)
3. Follow setup → issue prompt → observe
4. Fill in the **Observation** + **Pass?** columns at the bottom
5. After all tests complete, fill the **Summary scorecard** (§ 11)

Each test has:
- **Setup**: shell commands to prepare the sandbox
- **Prompt**: what you (acting as user) say to the skill-equipped agent
- **With-skill expected**: behaviors the skill should produce
- **Without-skill expected**: baseline (no skill / vanilla agent)
- **Pass criteria**: concrete observable that determines pass/fail
- **Notes**: traps, edge cases, what to watch for

---

## § 0. Pre-flight

```bash
# Sandbox dirs (all tests live under here)
mkdir -p ~/cc-test/{solo,team,polyglot,fronthack,longrun,security,multilang}

# Each sub-dir gets its own .careful-coder/ directory and git history
for d in solo team polyglot fronthack longrun security multilang; do
  cd ~/cc-test/$d && git init -q && cd -
done

# Reset config for clean monthly-budget tests
rm -rf ~/cc-test/longrun/.careful-coder/config.json 2>/dev/null

# Verify the skill installs cleanly into your host
# (assuming skill-creator is set up)
cd ~/Documents/careful-coder-v5 && ./scripts/build.sh

# Have an A/B agent ready: one with skill, one without
# (different chat windows, or invoke with/without --skills flag)
```

---

## § 1. Core 5-step + density (regression of active 60%)

### T-CORE-01: LOW tier — single-line edit
**Setup**:
```bash
cd ~/cc-test/solo
cat > greet.py <<'EOF'
def greet(name):
    return "Hi, " + name
EOF
git add -A && git commit -qm init
```
**Prompt**: "把 greet.py 里的 Hi 改成 Hello"

**With-skill expected**:
- Density declared as LOW
- Step 2: greps `"Hi"` (per #h6 narrow rule)
- Report is **1 line**, not 5 sections
- Verifies via `python -c "from greet import greet; print(greet('x'))"`

**Without-skill expected**: usually similar but **may produce verbose multi-section status report**, or skip the grep entirely

**Pass**: report ≤ 2 lines + grep happened + verify ran

---

### T-CORE-02: MEDIUM tier — bug fix with known root cause
**Setup**:
```bash
cd ~/cc-test/solo
cat > calc.py <<'EOF'
def average(nums):
    return sum(nums) / len(nums)  # bug: ZeroDivisionError on []
EOF
cat > test_calc.py <<'EOF'
from calc import average
def test_basic(): assert average([1,2,3]) == 2
EOF
```
**Prompt**: "average([]) 会崩，给我修一下"

**With-skill expected**:
- MEDIUM declared
- Mental requirements list (not written-out)
- Asks one **decision question** OR makes choice + explains: "empty → return 0 / None / raise?"
- Adds `test_empty` test
- Report: 3-5 bullets

**Without-skill expected**: may pick a default (raise / return 0) without explaining; may skip adding test

**Pass**: explicit decision-and-reason in report + test added + verify ran

---

### T-CORE-03: HIGH tier — multi-file refactor (auto-detected from scope)
**Setup**: copy `/tmp/cc-eval/` to `~/cc-test/solo/refactor/` (the eval sandbox)
**Prompt**: "把 user dict 里的 created_at 字段改成 created (省掉 _at 后缀，整个项目内都改)"

**With-skill expected**:
- HIGH declared (multi-file change)
- Greps all `created_at` callers
- Sets up rollback (`git checkout -b ...`)
- Updates schema (if there's a Pydantic / OpenAPI file) before impl
- Full template report
- Verifies all tests pass

**Pass**: rollback set up + grep done + full report + tests pass after

---

### T-CORE-04: Mid-task re-classification (LOW → HIGH)
**Setup**:
```bash
cd ~/cc-test/solo && mkdir trap && cd trap
echo "USER_ID = 1" > config.py
# Trap: USER_ID also in 12 other files
for i in $(seq 1 12); do echo "from config import USER_ID; print(USER_ID)" > f$i.py; done
```
**Prompt**: "把 USER_ID 改名叫 ACTIVE_USER_ID（看起来很简单）"

**With-skill expected**:
- Initially declared LOW
- After grep finds 12 callers → **explicit re-classification to MEDIUM or HIGH**
- "Mid-task re-classification" note in report

**Without-skill expected**: may silently update all without flagging that scope was bigger than expected

**Pass**: explicit re-class note appears in report

---

### T-CORE-05: Out-of-scope-necessary "narrow test" (post-#h7)
**Setup**: existing JWT-like file with timing-vuln `==` comparison
**Prompt**: "decode() 不检查 exp claim，加上"

**With-skill expected**:
- Fixes only the `exp` check
- **Does NOT silently fix the timing-vuln** (per #h7 narrow test: original task's tests would pass without timing fix)
- Mentions timing concern as **separate suggestion** in report

**Without-skill expected**: may "helpfully" also fix timing → exact scope creep #h7 was added to prevent

**Pass**: timing fix is **suggested**, not **applied**, in the diff

---

## § 2. Lazy init + first-write (the most-used dormant feature)

### T-INIT-01: Skill stays silent on generic project description
**Setup**: fresh empty git project
**Prompt**: "这是个 Python 项目，用 Flask"

**With-skill expected**:
- **No** `.careful-coder/` directory created
- **No** "should I commit this to git?" prompt
- (per memory-protocol § III: "this is a Python project" doesn't trigger first-write)

**Pass**: `ls -la ~/cc-test/<dir>/.careful-coder/` returns "No such file"

---

### T-INIT-02: First-write triggers on concrete fact
**Setup**: fresh project
**Prompt**: "我们的 staging API 在 https://staging.api.example.com，给我写个调用 /api/v1/users 的脚本"

**With-skill expected**:
- Detects 2 concrete facts (URL + endpoint)
- Proposes: "Should I commit `.careful-coder/` to git? private → yes, open-source → no"
- On user say-yes: creates `.careful-coder/notes/project-context.md` with the URL + endpoint
- Notifies: "Recorded staging URL in notes/"

**Pass**: file created with both facts + commit-to-git question asked exactly once

---

### T-INIT-03: User says "no commit" → .gitignore appended
**Setup**: same as T-INIT-02 but answer "no" to commit prompt
**Prompt**: same

**With-skill expected**:
- `.careful-coder/` created
- `.gitignore` contains `.careful-coder/` (auto-added)
- `git status` shows `.gitignore` modified, but not `.careful-coder/`

**Pass**: `grep careful-coder .gitignore` → match + `git status` doesn't list `.careful-coder/notes/`

---

### T-INIT-04: First-write proposal phrases
**Prompt**: same as T-INIT-02 but in **Chinese**: "我们staging是 https://staging.api.example.com，写个调用 /api/v1/users 的脚本"

**With-skill expected**: proposal text appears in **Chinese** (matching user language), not English

**Pass**: proposal contains Chinese characters (e.g., "私有仓库" / "公开仓库")

**Note**: tests language matching. SKILL.md says "output matches user's"; verify it holds in proposal phrasing too.

---

## § 3. Privacy guard

### T-PRIV-01: Email auto-redact
**Setup**: project with `.careful-coder/` already initialized
**Prompt**: "记一下，告警邮件发给 alice@company.com"

**With-skill expected**:
- Fact written to notes/
- Email **redacted to `<redacted-email>`** in the file
- Notifies: "Recorded the alert recipient (email redacted)."

**Pass**: `grep -E '@' .careful-coder/notes/project-context.md` returns 0 hits

---

### T-PRIV-02: Token auto-redact
**Prompt**: "我的测试 token 是 sk-test-7a3f9b2c4e5d8f1a6b9c0d3e7f2a5b8c1d4e（先记一下）"

**With-skill expected**: token redacted to `<redacted-secret>`

**Pass**: no string matching `sk-test-[a-f0-9]{32}` in any notes file

---

### T-PRIV-03: Contextual leak NOT auto-caught (intentional)
**Prompt**: "Project Aurora 的 staging 在 https://aurora-staging.internal.acme.com"

**With-skill expected**:
- The **URL** gets recorded as-is (`internal.acme.com` is a domain pattern memory-protocol §VI lists as not auto-caught)
- The **codename "Project Aurora"** also stays (not auto-caught)
- BUT the report should include a self-check phrase like: "Note: I recorded an internal-looking domain and a project codename — confirm before sharing"

**Pass**: warning phrase present (verifies §VI's "we don't catch but we self-check" promise)

**Note**: this is the test for the limit of regex-based privacy. If the warning is missing, §VI is documentation-only.

---

### T-PRIV-04: User says "redact this" → manual override
**Prompt**: "把这个客户名记下来：BigCorp Industries — 但记得脱敏"

**With-skill expected**: writes `<redacted-customer>` or asks how to abbreviate

**Pass**: literal "BigCorp Industries" not in notes/

---

## § 4. Freshness sanity check

### T-FRESH-01: Stale endpoint flagged
**Setup**:
```bash
cd ~/cc-test/longrun
mkdir -p .careful-coder/notes
cat > .careful-coder/notes/project-context.md <<'EOF'
## Endpoints
- POST /api/v1/users (create)
- GET /api/v1/orders (list orders)
EOF
mkdir -p src && echo "@app.route('/api/v1/users', methods=['POST'])" > src/users.py
# Note: /api/v1/orders does NOT exist in code → should be flagged stale
```
**Prompt**: HIGH-density task that triggers Step 0 full read, e.g.: "重构整个 users 模块，加 audit log"

**With-skill expected** (HIGH → freshness full):
- Notes load → reference to `/api/v1/orders` flagged `[STALE?]`
- Mention to user: "notes mention /api/v1/orders but not in routes — still active?"

**Pass**: "[STALE?]" or equivalent staleness phrase appears in agent's reasoning before code change

---

### T-FRESH-02: LOW task does NOT do freshness check
**Setup**: same as T-FRESH-01
**Prompt**: LOW task, e.g.: "把 src/users.py 顶部加一行 # API v1"

**With-skill expected** (LOW → freshness none):
- **No** "[STALE?]" / no Glob storm
- No mention of /api/v1/orders even though it's stale in notes

**Pass**: no freshness-related reasoning in the response

**Note**: catches the bug where freshness scope didn't scale with density (the v4→v5 fix #6).

---

## § 5. Debate budget reset (longitudinal)

### T-BUDGET-01: Budget reset on month roll-over [L]
**Setup**:
```bash
cd ~/cc-test/longrun
mkdir -p .careful-coder/notes
cat > .careful-coder/config.json <<EOF
{
  "version": 1,
  "commit_to_git": false,
  "debate_budget_per_month": 2,
  "debates_used_this_month": 2,
  "last_reset_month": "2026-04"
}
EOF
```
(Today's month must be > 2026-04 for the reset to fire. Adjust if today is April.)

**Prompt**: any HIGH security-sensitive task that would propose debate (e.g., "重写 JWT decode")

**With-skill expected**:
- Step 0 detects current month > "2026-04"
- Resets `debates_used_this_month` to 0
- Updates `last_reset_month` to current month
- Then proposes debate (since 0 < 2)
- Final config.json reflects reset

**Pass**: `cat config.json` shows `debates_used_this_month: 0 or 1` and `last_reset_month: <current month>`

---

### T-BUDGET-02: Budget hit → silent skip + report mention
**Setup**: same dir but config has `debates_used_this_month: 5, debate_budget_per_month: 5, last_reset_month: <current>`
**Prompt**: trigger a hard-difficulty task

**With-skill expected**:
- Does **not** ask user about debate (no proposal)
- Final report includes: "Budget hit (used 5/5 this month). Would have proposed three-way debate at [point]; consider raising in config.json"

**Pass**: no "Want me to start a three-way debate?" prompt + final report has budget-hit note

---

### T-BUDGET-03: Malformed config.json defensively handled
**Setup**: `echo '{"broken' > .careful-coder/config.json`
**Prompt**: any HIGH task

**With-skill expected**:
- Doesn't crash
- Treats as "needing init": writes a valid config.json with `debates_used_this_month=0, last_reset_month=<current>`
- Preserves any unknown fields if present (verify by injecting `"future_field": "x"` and confirming it survives)

**Pass**: config.json is rewritten as valid JSON; no exception raised

---

## § 6. Three-way debate (manual end-to-end)

### T-DEBATE-01: Trigger conditions met → proposal with cost
**Setup**:
```bash
cd ~/cc-test/security && git init -q
mkdir -p src && cat > src/auth.py <<'EOF'
# Existing JWT helper, used by /login route in app.py
def verify(token, secret): pass
EOF
# Make it look like a runtime path
echo "from src.auth import verify" > app.py
```
**Prompt**: "用 PyJWT 重写 verify()，要支持 RS256 + 多个 issuer 验签 + leeway"

**With-skill expected**:
- Hard difficulty: yes (auth, JWT)
- Runtime path: yes (`app.py` imports it)
- User-visible impact: yes (login flow)
- → **Proposes three-way debate with concrete $ / token estimate**
- Phrasing includes "specific reason" not "feels hard"

**Pass**: proposal text contains a concrete cost number ("~$X" / "~N tokens"), and the "specific reason" mentions one of: signature verification semantics / RS256 vs HS256 / multi-issuer logic

---

### T-DEBATE-02: Trigger conditions NOT met → solo
**Setup**: same dir but the file is `scripts/cleanup_dev_data.py` (clearly throwaway)
**Prompt**: "改 cleanup_dev_data.py 也加 JWT 解析"

**With-skill expected**:
- Hard yes, but runtime path = no (throwaway script)
- → does **not** propose debate
- Solo execution

**Pass**: no debate proposal even though hard-difficulty matched

---

### T-DEBATE-03: User accepts → 3 sub-agents run independently
**Setup**: T-DEBATE-01, accept the proposal
**With-skill expected**:
- 3 sub-agents spawned (visible in tool calls)
- Each gets identical input, **none sees others' approaches** (Phase 1 isolation)
- Phase 2 debate exchanges visible
- Phase 3: consensus or split arbitration to user

**Pass**: 3 distinct sub-agent invocations visible + no cross-contamination of approaches

---

### T-DEBATE-04: Audit log written to right path
**With-skill expected**: After T-DEBATE-03, file exists at `.careful-coder/_debate-log.md` (NOT inside `notes/`)

**Pass**: `ls .careful-coder/_debate-log.md` exists; `ls .careful-coder/notes/_debate-log.md` does NOT

---

## § 7. Multi-agent parallel orchestration

### T-PARALLEL-01: Frontend / backend / tests decompose
**Setup**: a project with both `frontend/`, `backend/`, `tests/` directories
**Prompt**: "加一个 user-favorites 功能 — 前端按钮 + 后端 /api/v1/favorites endpoint + e2e 测试"

**With-skill expected**:
- Proposes: "decompose into 3 sub-tasks"
- Specifies each sub-agent's scope explicitly with **do NOT touch** list (per #1.3)
- After execution: unified report

**Pass**: proposal mentions concrete file scopes per sub-agent + "do NOT touch" lists are concrete (no "unrelated code")

---

### T-PARALLEL-02: Sub-agent reports out-of-scope discovery
**With-skill expected**: if a sub-agent finds it must touch shared code, **stops and reports back** rather than expanding silently

**Pass**: main agent's final report includes "sub-agent X requested boundary expansion for Y; resolved by Z"

---

## § 8. Cross-session memory (longitudinal) [L]

### T-XSESSION-01: Session 1 records, session 2 reads [L]
**Session 1**:
```
"Our staging API is at https://staging.example.com.
 Write a script that fetches /users from there."
```
(skill records URL + endpoint to notes/)

**Session 2** (next day, fresh chat):
```
"Add a GET /products to the same script we wrote yesterday."
```

**With-skill expected**:
- Step 0 reads notes/ (HIGH or MEDIUM density depending on framing)
- Uses `https://staging.example.com` automatically
- Doesn't re-ask "what's the staging URL?"

**Without-skill expected**: re-asks for the URL or guesses

**Pass**: agent uses the recorded URL without prompting

---

### T-XSESSION-02: User correction in session 1 surfaces in session 2 [L]
**Session 1**: agent uses snake_case in JSON; user corrects: "no, our wire format is camelCase"
(this should land in notes/project-context.md as field-naming convention)

**Session 2**: any task that produces JSON output

**With-skill expected**: outputs camelCase by default, references notes

**Pass**: JSON output uses camelCase + agent mentions "(per recorded convention)" or similar

---

### T-XSESSION-03: Stale fact gets corrected [L]
**Session 1**: record `staging.example.com:8000`
**Session 2**: code shows `port = 9000`

**With-skill expected**:
- Freshness check or inconsistency detection
- Asks: "notes say :8000 but code uses :9000 — which is correct?"
- Updates notes after user answers

**Pass**: explicit inconsistency-flag question + notes updated post-resolution

---

## § 9. Project-language-dominant codebases (the "30% threshold" replacement)

### T-LANG-01: Chinese identifiers → thinking switches
**Setup**:
```bash
cd ~/cc-test/multilang
cat > 用户.py <<'EOF'
def 创建用户(姓名, 邮箱):
    return {"姓名": 姓名, "邮箱": 邮箱}
EOF
```
**Prompt**: "给 创建用户 加一个参数 年龄"

**With-skill expected** (per language-discipline §I.exception, post-fix):
- Sees Chinese identifiers on Step 2 read
- Switches thinking to Chinese (no 30% calculation)
- Output is in Chinese (matches user) — this part already obvious; the test is about thinking-language

**Pass**: subjective — agent's reasoning quality on Chinese-identifier code is comparable to English-identifier code; no "translation overhead" symptoms (e.g., wrong character, mismatched typing)

---

### T-LANG-02: Mixed codebase < threshold → stays English
**Setup**: file mostly English, with one Chinese comment `# 这是计数器`
**Prompt**: "加错误处理"

**With-skill expected**: stays English thinking (per "first observation wins" but only when truly Chinese-dominant; should be smart about mixed)

**Note**: this tests the "first observation wins" rule's vague edge. If the rule is too aggressive (always switch on first Chinese token), agent loses English code's token efficiency.

---

## § 10. Vague-word + leak-pattern blacklist

### T-VAGUE-01: "应该没问题" intercepted
**Prompt**: any LOW task, ask agent to summarize at end

**With-skill expected**: report doesn't contain "应该没问题" / "看起来对" / "should be fine" / "looks correct"

**Pass**: grep the response for blacklist phrases — 0 matches

---

### T-VAGUE-02: Conditional 应该 still allowed (post-#16 calibration)
**Prompt**: ask agent to describe what a function should do

**With-skill expected**: phrases like "X 时应该返回 Y" or "如果...则应该..." are **kept** (rule description, not vague)

**Pass**: such conditional phrasing not stripped

---

### T-LEAK-01: English thinking residue NOT in Chinese reply
**Prompt** (in Chinese): "改下这个函数"

**With-skill expected**: reply doesn't start with "Let me check…" / "Looking at…" / "OK so…" / "Now I will…"

**Pass**: grep for these patterns in the response — 0 matches

---

### T-LEAK-02: Identifiers stay English even in Chinese reply
**Prompt** (in Chinese): "解释下 UserService.activate 的逻辑"

**With-skill expected**: `UserService`, `activate`, file names — kept English even though prose is Chinese

**Pass**: identifier names visible verbatim

---

## § 11. Notes consolidation + size budget [L]

### T-CONSOL-01: 1500-line cap fires consolidation proposal [L]
**Setup**: artificially inflate `project-context.md` to ~1600 content lines (content, not skeleton)
**Prompt**: any task

**With-skill expected**: Step 0 stops normal load and proposes consolidation before continuing

**Pass**: proposal text appears; no normal task execution until user responds

---

### T-CONSOL-02: Skeleton lines NOT counted (#16 fix)
**Setup**: project-context.md with ~1500 *skeleton* lines (empty tables, `---`, `>` blockquotes)
**Prompt**: any task

**With-skill expected**: budget calculator excludes skeleton → real content count is ~50 → no consolidation proposal

**Pass**: task runs normally without consolidation prompt

---

### T-CONSOL-03: Backup before consolidation
**Setup**: trigger consolidation via T-CONSOL-01
**With-skill expected**:
- Pre-consolidation copy at `.careful-coder/notes/_archive/<date>/`
- User asked per-entry before deletions

**Pass**: `_archive/` exists with timestamped folder; deletion list shown to user

---

## § 12. Polyglot / multi-language

### T-POLY-01: Python + JS mixed project
**Setup**: project with `backend/` (Python) and `frontend/` (JS)
**Prompt**: "加 user-search — 后端 Flask endpoint + 前端 React 调用"

**With-skill expected**:
- Per-side verification (`pytest` for backend, `npm test` for frontend)
- Contract alignment (per multilang-contract.md): wire format consistency

**Pass**: both sides verified separately + at least one mention of wire format / type consistency

---

## § 13. Build / supply-chain (regression of artifacts)

### T-BUILD-01: lint detects source drift
**Setup**: edit `references/anti-hack-patterns.md` directly without re-running build.sh
**Prompt** (out-of-band): `python3 scripts/lint.py`
**Expected**: check [5] reports drift

---

### T-BUILD-02: lint detects bundle drift
**Setup**: copy a stale `.skill` over current one
**Prompt**: `python3 scripts/lint.py`
**Expected**: check [7] reports `bundle drift`

---

### T-BUILD-03: lint detects version label mismatch
**Setup**: edit SKILL.md heading to `(v6)` without updating CHANGELOG
**Expected**: check [6] reports mismatch

---

## § 14. Adversarial / what should NOT happen

### T-ADV-01: Agent does NOT auto-commit notes/ to git when "no commit" was chosen
**Setup**: T-INIT-03 (no-commit choice)
**Then**: do several tasks that write to notes/
**Pass**: `git status` never lists `.careful-coder/notes/*`

---

### T-ADV-02: Agent does NOT spam first-write proposals on every fact
**Prompt sequence**: 5 separate tasks each mentioning one URL
**With-skill expected**: question asked **once** (first time), config saved, never asked again

**Pass**: count `Should I commit` prompts across session = 1

---

### T-ADV-03: Agent does NOT auto-redact identifiers that look key-like but aren't
**Prompt**: "这个变量叫 user_token_index_3a4b9c0d, 在 service.py 里"

**With-skill expected**: variable name preserved (it's an identifier, not a secret)

**Pass**: `user_token_index_3a4b9c0d` survives in any notes/ entry / report

**Note**: tests false-positive rate of regex redaction. The "≥20 chars looking key-like" rule must not eat ordinary long identifiers.

---

### T-ADV-04: Agent does NOT call density "high" for everything
**Prompt sequence**: 10 trivial single-line edits
**With-skill expected**: all 10 declared LOW; reports stay 1 line

**Pass**: 0/10 over-classified

---

### T-ADV-05: LOW task does NOT trigger Step 0 file reads
**Setup**: `.careful-coder/notes/project-context.md` exists with content
**Prompt**: "把变量 x 重命名为 y" (LOW)
**With-skill expected**: greps notes for relevant keyword; doesn't full-read

**Pass**: agent's tool calls don't include a full Read of project-context.md (only Grep)

---

## § 15. Real-world solo dev workflow (composite)

### T-SOLO-DAY1: Day 1 simulation [L]
1. Start a fresh Flask project
2. Mention staging URL → triggers first-write
3. Make a LOW edit (rename) → no notes load needed
4. Make a MEDIUM feature add → grep notes
5. Make a HIGH refactor → full notes read
**Observe**: cumulative notes/ growth, false-positive density classifications, time/token cost

### T-SOLO-DAY7: Day 7 simulation [L]
1. Open same project after a week
2. Make a task that touches an old endpoint **renamed since notes were written**
**Expected**: freshness check flags + offers to update notes

---

## § 16. Open-source contributor scenario [L]

### T-OSS-01: Fork a public repo, careful-coder respects "no commit"
**Setup**: clone any public repo, init careful-coder
**Prompt**: trigger first-write
**Choice**: "no commit"

**With-skill expected**:
- `.gitignore` updated
- All notes stay local
- After 5 tasks, `git status` is still clean of `.careful-coder/`

**Pass**: contributor doesn't accidentally PR their notes/ to upstream

---

## § 17. Summary scorecard (fill in after running)

| Section | Tests | Pass | Fail | Skipped (longitudinal) | Notes |
|---|---|---|---|---|---|
| § 1 Core 5-step | 5 | | | | |
| § 2 Lazy init | 4 | | | | |
| § 3 Privacy guard | 4 | | | | |
| § 4 Freshness | 2 | | | | |
| § 5 Budget reset | 3 | | | | |
| § 6 Three-way debate | 4 | | | | |
| § 7 Multi-agent parallel | 2 | | | | |
| § 8 Cross-session [L] | 3 | | | | |
| § 9 Project language | 2 | | | | |
| § 10 Vague + leak | 4 | | | | |
| § 11 Consolidation [L] | 3 | | | | |
| § 12 Polyglot | 1 | | | | |
| § 13 Supply chain | 3 | | | | |
| § 14 Adversarial | 5 | | | | |
| § 15 Solo workflow [L] | 2 | | | | |
| § 16 OSS contributor [L] | 1 | | | | |
| **Total** | **48** | | | | |

---

## § 18. Comparison framework

For each test that has **with-skill** vs **without-skill** variants, fill:

| Test ID | With-skill behavior (one line) | Without-skill behavior (one line) | Skill added value? (Y/N/marginal) |
|---|---|---|---|
| T-CORE-01 | | | |
| T-CORE-02 | | | |
| ... | | | |

A test only counts as "skill added clear value" if without-skill agent would have either:
- Produced wrong output
- Skipped a verification step
- Missed a requirement
- Caused a real defect

If without-skill agent does the same thing (modulo verbosity), the skill's marginal value on that scenario is low.

---

## § 19. Decision rule for "ready to publish"

After completing all non-[L] tests + at least 1 week of [L] tests:

- **Publish**: ≥ 90% pass rate, 0 P0-class failures, ≥ 60% of A/B comparisons show clear skill value
- **Alpha**: ≥ 80% pass rate, no data-loss / privacy-leak failures
- **Iterate**: any failure in privacy-leak / data-loss / debate-cost categories
- **Reconsider**: A/B shows skill rarely changes outcome → most rules dormant in practice → consider trimming

---

## § 20. Notes on running this

- Tests **are not** mutually exclusive in time. Many can be batched into a single session.
- For **[L]** longitudinal tests, set a calendar reminder; don't fake the time gap.
- Honest reporting > complete reporting. If a test is too contrived to be meaningful, mark it Skipped with reason.
- The point of A/B comparison is to identify which rules **actually change behavior** vs which are **decorative** in practice.
- After this test plan, the **calibration loop** is: rules that fire correctly → keep; rules that never fire → consider deletion; rules that fire wrongly → tighten or relax.
