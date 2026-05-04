# careful-coder Changelog

记录 v1 → v2 → v3 → v4 → v5 的设计变更与原因。新版本永远在最上面。

---

## v5.1-beta — Released 2026-05-05 (current)

Cost-reduction refactor. Same behavior, dramatically lower per-invocation token cost. No semantic changes to discipline; structural reorganization only.

### v5.1-beta hotfix-1 — RELEASE_NOTES drift catcher (2026-05-05)

The initial v5.1-beta release shipped with the GitHub release body still saying "v5.0-beta" because `RELEASE_NOTES.md` was never updated for the new version (the file's first H1 was stale). Tag and title were correct; only the body text was wrong. Forward-fix only — the live v5.1-beta release body remains as-shipped.

- **#h9** Rewrote `RELEASE_NOTES.md` for v5.1-beta — new heading, v5.1-beta-specific "what's new" content (size cuts, summary blocks, lint [8]/[9]/[10], `--strict`, release pipeline), updated install instructions and roadmap.
- **#h10** Added lint check `[10] RELEASE_NOTES version match` — first H1 of `RELEASE_NOTES.md` must declare the same version as `CHANGELOG.md`'s top `## vN` entry. Same meta-fix pattern as check `[6]` (SKILL.md vs CHANGELOG) and check `[9]` (README vs lint.py): every recurring drift class gets its own lint rule.
- README updated: `9 consistency checks` → `10 consistency checks` (caught automatically by check `[9]` once `[10]` was wired into main).

### Changes

- **#c1** SKILL.md slimmed from ~4634 tokens (v5.0-beta) to ~2893 tokens (**−38% on hot path**). Removed: `v5 highlights` paragraph (now in this CHANGELOG), `Why this skill exists` (now in README only), `Closing` paragraph, `Project memory` standalone section (was redundant with Step 0 + memory-protocol.md), `Further reading` table (compressed to inline note). Compressed: each Step's prose body (decision table is the source of truth; Steps now state the always-do invariants only). **Preserved verbatim**: frontmatter `description` (trigger accuracy), Density × Steps decision table, Thinking-flow 5 core points.
- **#c2** Each `references/*.md` now begins with a `<summary>` block (~150 tokens). Format: Contents enumeration / Read full when / Skim sufficient when. Lets Claude skim a reference and decide whether to deep-read — cuts cold-path load by an estimated 40% on MEDIUM-density tasks.
- **#c3** New lint check `[8] SKILL.md size guard`: soft-warn at 2700 tokens, hard cap at 3000. Catches future hot-path bloat at PR time.
- **#c4** Added `<!-- CACHE BOUNDARY -->` marker at the end of SKILL.md. Documents the design intent: SKILL.md content is static and cacheable; project-level injections (notes/) belong in user messages, not appended to SKILL.md.
- **#c5** Added `--strict` flag to `scripts/lint.py`. Default mode keeps lockfile-drift and missing-bundle as warnings (so first-time clones don't break). `--strict` promotes them to hard errors. `scripts/release.sh` and `.github/workflows/release.yml` now use `--strict`, so manual or CI releases cannot ship with a stale `.skill` bundle. Closes the gap that allowed shipping with a bundle older than source.
- **#c6** Added lint check `[9] README check-count consistency` — self-referential drift catcher. Scans `lint.py` for the actual number of checks and `README.md` for "N checks" / "N consistency checks" claims; fails if mismatch. Catches the exact pattern that almost slipped through review for v5.1-beta (README still said "7 checks" after check [8] landed). Total checks: **9** (was 7 in v5.0-beta).

### What did NOT change

Discipline, decision rules, density classification, all 7 references' actual content (only added summary headers), templates, scripts/build.sh, evals/. Behavior is identical to v5.0-beta; this is a pure cost-reduction pass.

### Estimated savings (per task, post-cache)

| Density | v5.0-beta overhead | v5.1-beta overhead (no cache) | v5.1-beta + 80% cache hit |
|---|---|---|---|
| LOW | ~4700 tokens | ~2900 tokens | ~700 tokens |
| MEDIUM | ~7500 tokens | ~4400 tokens | ~1500 tokens |
| HIGH | ~11000 tokens | ~6800 tokens | ~2900 tokens |

Cache savings depend on the host actually applying prompt cache to skill content; the marker documents intent.

### Roadmap to v5.2

Modality 3 from the cost-reduction plan: ship 3 deterministic scripts that replace LLM-token work with bash exec — `freshness-check.py`, `diff-noise-detector.py`, `notes-size-check.py`. SKILL.md will reference these in Step 0 and Step 4 with "try the script first, fallback to LLM".

---

## v5.0-beta — Released 2026-05-04

First public Beta release. All v5 features below are included. Beta tag reflects: ~40% of features (cross-session memory, debate-budget reset, freshness check, consolidation, multi-agent) require longitudinal validation that single-session A/B sandbox cannot provide. Roadmap: 1-2 weeks of [L] longitudinal eval → v5.0-stable. See `README.md` § Known limitations.

---

## v5 — Bug fixes + supply-chain hygiene

### v5.1 hotfix-2 — Calibration from live eval (2026-05-04)

Based on a live N=5 eval against a sandbox Flask project. The eval found 1 real flaky-test bug (caught by ★★★ rule), 1 self-admitted scope-creep (Task 3 timing-attack drive-by), and 1 silent-verification scenario (pytest tests skipped by `unittest discover`). 3 highest-ROI calibration fixes applied in place:

- **#h6** SKILL.md decision table: LOW Step 2 changed from "skip read unless public API" → "**always Grep the symbol; skip the full Read**". Renames break string-referenced sites (test fixtures, configs, dynamic attribute access) regardless of public/private.
- **#h7** `anti-hack-patterns.md` § 2.4: out-of-scope-necessary now requires a **narrow test** — "the original task's own tests cannot pass without this change". Includes a Pass example (true inseparable) and a Fail example (the eval's own Task 3 timing-attack fix as a cautionary case study).
- **#h8** `self-check-protocol.md` § I: new "Test-discovery sanity check" — `0 tests ran` exit-0 is **not** ★★ pass; treat as fallback to ★ tier with explicit explanation. Covers `unittest discover` missing pytest tests, missing test directories, missing test scripts, etc.

These three together address the most concrete failure modes observed in single-session use. Other items from the eval report (`§3.2`/`§3.4`/`§3.6`/`§3.7`/`§3.8`/`§3.9`/`§3.10`) are calibration deferred to longitudinal data — not enough signal in N=5 to commit.

### v5 hotfix (in-place, applied after initial v5 release)

In-place fixes to v5 itself based on a follow-up review:

- **#h1** SKILL.md heading was stuck at "(v4)" / "v4 highlights" / "v1 → v4" — bumped to v5 with v5-specific highlights
- **#h2** `scripts/build.sh` had a sandbox-specific path (`/sessions/...`) as the default `SKILL_PACKAGER` — replaced with a clean search order: `$SKILL_PACKAGER` → `$HOME/.claude/...` → `$XDG_DATA_HOME/...`
- **#h3** `build.sh` exited 0 when packager was missing (silent failure) — now exits 2 with a clear error
- **#h4** `memory-protocol.md` § IV.2 budget-reset assumed `config.json` is always well-formed — now defensively handles missing/malformed/future-version configs
- **#h5** lint didn't verify the `.skill` bundle matches the lockfile — `build.sh` now appends `## Bundle hash` to `careful-coder.lock`, and `lint.py` adds check [7] (bundle drift detection)
- New lint check [6]: SKILL.md `(vN)` heading must match `CHANGELOG.md`'s top `## vN` entry — prevents this exact category of drift from recurring

**触发**:对 v4 的 P0/P1/P2 评审(17 条)。

### Real bugs fixed (P0)

- **#1** `lint.py` 的 `find_section_refs()` 是 dead code → **删掉**(实际 anchor 校验代价大于收益)
- **#2** Debate budget 月度 reset 没触发机制 → `config.json` 加 `version` + `last_reset_month` + `debates_used_this_month`;Step 0 检查月份变化时 reset
- **#3** `_debate-log.md` 路径在 `notes/` 内会吃 size budget → 移到 `.careful-coder/_debate-log.md`(跟 `notes/` 平级)
- **#4** "silent + note in report" 自相矛盾 → 改成"don't propose; mention once in final report"

### Design fixes (P1)

- **#5** 模板中文混用 → 全部改成 **REQUIRED / 必填** + **OPTIONAL / 可选** 双语标签
- **#6** Step 0 freshness check 不跟 density 联动 → low 不做、medium 只对命中段、high 全量
- **#7** Mid-task re-classification 协议 → `language-discipline.md § II.4` 明确触发条件 + 行为(暂停 / 重 declare / 补做)
- **#8** "30% 非英语 identifier" 阈值无人执行 → 简化成"看到非英文 identifier/comment 就切换"
- **#9** Privacy guard contextual info 列举 → §VI 加 "what we DON'T catch" 清单(项目代号 / 客户名 / 同事名 / 内部域名 / Slack 频道 / Jira ID 模式)
- **#10** `.skill` 文件来源不明 → 加 `scripts/build.sh`(从源构建 .skill + 写 lockfile);CHANGELOG 说明
- **#11** eval HTML 在 skill 根目录 → 改成放在 host 机器的部署文件夹,**不进 .skill bundle**

### Polish (P2)

- **#12** `config.json` 加 `"version": 1`;v6+ 改 schema 时必须做 migration
- **#13** `_debate-log.md` 加模板 `assets/notes-templates/_debate-log.md`(空骨架 + entry format)
- **#14** debate 日志 "Result quality (user verdict)" 字段删掉(99% 时间收集不到 = 摆设)
- **#15** lint 跑 v5 全文件验证 → 0 issues(详见 lint 结果)
- **#16** size budget 1500 行**只算实质内容**:跳过空表行 / `---` / `(Auto-appended...)` 占位 / `[Example — auto-remove]` 块 / `>` blockquote
- **#17** SKILL.md decision table 加指针指向 `language-discipline.md § II.5`(per-tier forbidden behaviors),不再两边维护

### Cross-cutting

- **C** 新增 `careful-coder.lock`(每次 `build.sh` 重新写;sha256 of every source file)
- lint.py 加 lockfile freshness check(检测 `.skill` bundle 跟 source 漂移)

### Architecture

```
careful-coder-v5/
├── SKILL.md                    (主入口)
├── CHANGELOG.md                (本文)
├── careful-coder.lock          ← v5 新增,build.sh 自动写
├── careful-coder-v5.skill      ← 打包产物,build.sh 生成
├── references/                 (7 个深度文档)
├── assets/notes-templates/     (3 个模板,含新增 _debate-log.md)
└── scripts/
    ├── lint.py                 ← 4 道 check + lockfile freshness
    └── build.sh                ← 一条命令重建
```

---

## v4 — Tier-aware everything + privacy + audit (current)

**触发**:基于 v3 真实使用反馈的 P0/P1/P2/P3 评审(18 条 + 4 条跨条建议)。

### Breaking changes

- `.careful-coder/notes/` 默认**不再** commit 进 git;改成首次创建时 ask 用户一次,选择存到 `.careful-coder/config.json`。
- 报告格式从"五段式默认"改成"按 density 三档"(low / medium / high)。所有任务必须先做 density classification。
- Step 4 中 "Rollback safety check" 拆成两段:**setup before** 挪到 Step 1 / Step 2;Step 4 只做 "rollback path still clean?" 重确认。

### New features

- **Density × Steps decision table**(SKILL.md 顶部):每个 step 在 low/medium/high 三档下做什么、做多深,一表显示
- **Step 0 density-aware loading**:low → grep notes 关键词;medium → 读 project-context.md + grep tech-decisions;high → 全文读两个文件
- **Freshness sanity check**(memory-protocol.md §V):加载 notes 后,扫一遍引用的文件路径/函数/端点是否还存在,不存在标 `[STALE?]`
- **Notes/ size budget**(memory-protocol.md §VIII):总和 ≤ 1500 行,超出则 Step 0 强制提议 consolidation
- **Privacy guard**(memory-protocol.md §VI):写入前自动 redact 邮箱/电话/token/IP
- **Three-way debate cost estimate + budget + audit log**(multi-agent-protocol.md §II):
  - 提案模板必须含具体 token/$ 估算
  - 月度 budget 配置(`.careful-coder/config.json`)
  - 每次 debate 落账到 `.careful-coder/notes/_debate-log.md`
- **Multi-agent boundary derivation method**(multi-agent-protocol.md §I.1.3):明确怎么生成 sub-agent 的 do-NOT-touch 列表
- **Per-tier forbidden behaviors**(language-discipline.md §II.5):每档明确 do-NOTs,防止过度或欠缺执行
- **Density self-check**(language-discipline.md §II + §VI):任务完成后核对"实际工作是否匹配声明的 density"
- **Thinking-language exception**(language-discipline.md §I):非英语主导项目时,thinking 跟随项目语言(避免翻译开销)
- **Templates 必填/可选标注**(assets/notes-templates/):每个字段标 required/optional;skill 在第一次写真实条目时自动删除 `[Example — auto-remove]` 占位
- **scripts/lint.py**:静态扫 SKILL.md + references/,检测 (a) 同一规则多处定义不一致 (b) 跨文件引用失效

### Fixes

- **#3** SKILL.md 的"Don't skip just because small"与 language-discipline.md low density profile 字面冲突 → 统一到 density × steps 决策表;"don't skip"改成"don't omit entirely"且强调"depth scales by tier"
- **#15** Forbidden phrasings 列表 SKILL.md / self-check-protocol.md 重复 → SKILL.md 留指针,self-check-protocol.md §VI 单点维护
- **#16** 中文「应该」一刀切被禁过严 → context-sensitive(语言纪律 §III):软性回避语境禁用,条件陈述/规则描述保留
- **#17** Performance-sensitive 阈值随意触发 CRUD 项目 → 改成需要 profiler / 数据规模 / 用户明确需求等具体证据,纯结构性提示不算
- **#14** Rollback safety check 文字内容是"before changing"但放在 Step 4 → 拆分到 Step 1/2 + Step 4 重确认
- **#13** Thinking 一律英文对中文文档项目反而是开销 → 加 exception:项目代码/注释/文档以非英语为主时跟随
- **#18** Sub-agent boundary 没说怎么生成 → multi-agent-protocol §I.1.3 给具体方法

### Removed (deprecated v3 features)

(no removals — v4 is purely additive over v3)

### Known limitations

- Sub-agent context distribution仍依赖主 agent 手动整理,没有自动化
- Privacy guard 的 redact 是基于正则,无 LLM 参与,会漏掉 contextual sensitive info(如"给王经理的报价")
- size budget 1500 行是经验值,未在大量项目验证

---

## v3 — Tier-aware (released)

**触发**:用户给出 6 条反馈 —— skill 体量大、触发面宽、Step 0 强读三件、英文残留、整理阈值理想化、报告太长。

### Breaking changes

- 删除 `user-feedback-log.md` 模板及其相关协议(职责交还给 host auto-memory)
- 删除自动周期整理阈值(300 行 / 30 写入)→ 改成按需触发

### New features

- **Tier classification**(SKILL.md):trivial / standard / substantial 三档,每个 Step 按档执行
- **Lazy initialization for notes/**:不再首次进项目就创建空模板,等到有真东西才 ask + create
- **Pre-send English-leak check**(language-discipline.md §V):leak pattern 黑名单 + 检查程序
- **Division of labor with host memory**(memory-protocol.md §I):明确划分边界

### Fixes

- 跟 host auto-memory 双写问题(by 删 user-feedback-log)
- Step 0 三文件强读(by lazy init)
- 报告分档(trivial 1 行 / standard 3-5 bullets / substantial 完整模板)

---

## v2 — Full discipline (intermediate)

**触发**:用户在 v1 基础上补充了 14 + 6 条需求,需要全面架构重写。

### New features

- 五步纪律(Step 0 加载记忆;Step 1-4 立单 / 读上下文 / 写+验证 API / 完整自检)
- 思考流约定(英文 thinking + 三档密度 + 模糊词黑名单)
- 项目记忆机制(notes/ + 模板)
- 难点会诊(三方辩论)
- 多 agent 编排
- 7 个 references/ 文档

---

## v1 — Initial draft

最初的简单版本:Python 写代码自检 4 步纪律(立单/读上下文/验证 API/运行自检)。
