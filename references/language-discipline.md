# Language Discipline — English Thinking, Density Tiers, Vague-Word & Leak-Pattern Blacklists, Per-Tier Forbidden Behaviors

This document defines the language, density, and word-choice standards for the thinking flow.

<summary>
Contents:
- § I: language assignments (English thinking default + non-English-project exception + user override)
- § II: density tier definitions (LOW / MEDIUM / HIGH with profile + adaptive judgment template + density self-check)
- § II.4: mid-task re-classification (triggers, action, one-way upward only)
- § II.5: per-tier forbidden behaviors (LOW/MEDIUM/HIGH "do NOT" lists)
- § III: vague-word blacklist (English + Chinese, with "应该" exception for conditional statements)
- § IV: standard "I don't know" phrasings (EN + CN templates)
- § V: pre-send English-leak check (allowed-English identifiers + leak-pattern table + check procedure)
- § VI: 6 self-check questions

Read full when: designing density classification for a borderline task; user reported leaked English; vague language was flagged in last reply; need exact "应该" allowed/forbidden cases.
Skim sufficient when: just need a quick reminder of the vague-word substitution; § headings tell you where.
</summary>

---

## I. Language assignments

| Context | Language |
|---|---|
| Thinking / scratchpad / internal reasoning | **English by default** (see exception below) |
| Reply to the user | **Match user's input language** |
| Code comments | Match the project's existing comment language |
| commit messages / PR titles | Default English, unless project conventions say otherwise (`notes/project-context.md`) |
| Error logs / user-visible error messages | Match the user's reply language |

### Why English by default for thinking

- **Higher token density**: English uses ~30-50% fewer tokens than Chinese / CJK languages for the same information; lets you fit more context into reasoning
- **Native technical vocabulary**: Most library docs, error messages, and API names are English; thinking in English avoids translation overhead
- **Reasoning stability**: Most code-related training data is English-dominant

### Exception: project-language-dominant codebases

If the project itself is **predominantly non-English** — Chinese variable names, Chinese-language comments, Chinese-only documentation — switch thinking to the project's language. The translation overhead of mapping Chinese symbols to English thinking and back outweighs the token-density benefit.

How to detect (no formal scan needed): when you Read the first file as part of Step 2, if you see **any non-English identifier OR any non-English comment**, switch thinking to the project's language for the rest of this task. No 30% calculation; first observation wins. (Earlier drafts specified a 30% threshold but it required a separate scanning pass that nobody actually ran — the simple heuristic does the same work for less.)

### Exception: explicit user override

If the user explicitly asks for thinking in another language ("think in Chinese too"), comply.

---

## II. Density tiers (used by the SKILL.md decision table)

Tier names are: **low (trivial)**, **medium (standard, default)**, **high (substantial)**.

### LOW (trivial) — when

- Editing copy / comments / minor styling
- Renaming a variable
- Deleting dead code
- Adding a single comment
- Fixing a typo

**Profile:** few lines of thinking; act. The SKILL.md decision table specifies which version of each step runs at this tier.

### MEDIUM (standard, default) — when

- Adding a new feature (single-file change)
- Fixing a bug (root cause known)
- Running a data script
- Calling a less-familiar library's common API

**Profile:** 100-300 words of thinking; mental requirements list (not written out long-form); 1-2 API verifications if needed; one self-check pass.

### HIGH (substantial) — when

- Hitting any hard difficulty in `difficulty-criteria.md`
- Multi-file / multi-module change
- Frontend↔backend contract change
- Requirements list ≥ 6 items, or scope is genuinely ambiguous
- > ~100 LOC delta

**Profile:** ≥ 500 words of thinking; written-out lists; multiple API verifications; possibly debate proposal.

### Adaptive judgment template

In thinking, first line of the task:

```
Density assessment:
- Task type: [single-file edit / multi-file refactor / bug fix / new feature / etc]
- Hard points hit: [none / list]
- Files involved: [count]
- Ambiguity in user request: [none / minor / significant]
→ Density: [low / medium / high]
```

### Density self-check (after task completion)

After finishing, verify:

```
Density check:
- Declared density: [low / medium / high]
- Actual work: [list what was done]
- Match? [yes / no, why not]
```

If declared `low` but you ended up doing a multi-file change → you should have re-classified mid-task (see § II.4 below). Note this in the report.

If declared `high` but actually only changed one line + a one-liner test → over-classification, wasted tokens. Note this and downgrade next time.

---

## II.4. Mid-task re-classification

The initial density classification is a hypothesis, not a contract. As the task proceeds, you may discover the actual scope is bigger or smaller than expected. **When that happens, re-classify mid-task and adjust your remaining steps.**

### Triggers for re-classification

Pause and re-classify when any of the following appears mid-task:

- **Scope grew**: declared LOW, but Step 2 grep finds the symbol used in ≥ 4 files, or a single-file edit reveals the file is part of a contract that touches frontend + backend
- **Hard difficulty appeared**: declared LOW or MEDIUM, but the implementation actually touches concurrency / async / security / a complex state machine (any item in `difficulty-criteria.md` § I)
- **Edge cases multiplied**: the requirements list you started with had 3 items, but you keep finding "oh and also …" as you read the code; if you're at 6+ items, you're probably HIGH
- **Time / token budget exceeded**: if you've spent 2× the typical effort for the declared tier, that's a strong signal you mis-classified

### Re-classification action

When a trigger fires:

1. **Stop the current operation** (don't keep coding under the wrong tier)
2. **Note the trigger explicitly in thinking**:
   ```
   Mid-task re-classification:
   - Declared: <old tier>
   - Trigger: <which trigger fired, with concrete evidence>
   - New tier: <new tier>
   ```
3. **Catch up on previously-skipped steps**:
   - LOW → MEDIUM: write the (mental) requirements list more explicitly; do the Step 2 read you skipped
   - MEDIUM → HIGH: write out the full requirements + scope boundary; do the contract alignment check; set up rollback if not already
   - LOW → HIGH: do both of the above, and consider whether difficulty consultation should be proposed
4. **Inform the user briefly** in the final report:
   > "Started at LOW tier (rename), but discovered the symbol is used across X files including a public API; bumped to MEDIUM and re-checked all callers."

### Don't downgrade mid-task

Re-classification is one-way (upward). If you declared HIGH and the work turns out simpler, finish the HIGH-tier discipline anyway — switching down mid-task risks dropping a step you already started.

---

## II.5. Per-tier forbidden behaviors

Each tier has explicit "don'ts" to prevent over- or under-engineering:

### At LOW tier, do NOT

- Build a written-out 7-item requirements checklist for a one-line rename
- Run a full pytest suite for a comment-only edit
- Write a 5-section status report
- Spawn sub-agents

### At MEDIUM tier, do NOT

- Skip the API verification when calling an unfamiliar method
- Skip the post-write run / import check
- Write a 5-section report when 3-5 bullets cover it
- Skip reading the file you're modifying

### At HIGH tier, do NOT

- Skip Step 2 contract alignment when changing front↔back interfaces
- Skip diff self-review
- Skip rollback path setup before changing
- Compress the report into 3 bullets

---

## III. Vague-word blacklist

The following are **forbidden in user-facing replies and reports**. They should also be avoided in thinking (since thinking is English, the English list matters most).

### English blacklist

| Vague word | Replacement |
|---|---|
| "I think" | State the fact directly, or write "I don't know — need to verify by X" |
| "maybe" | "this could happen if X" or "uncertain — depends on Y" |
| "probably" | Give a probability or condition, or admit unknown |
| "should work" | "I tested it and it works" or "untested — please verify" |
| "let me try" | "running X to verify" |
| "it's likely" | Same as probably |
| "I believe" | Same as I think |
| "kind of" / "sort of" | Delete, or be specific |
| "should be fine" | Run it first |
| "looks correct" | Run it first |

### Chinese blacklist (context-sensitive — see exception below)

| Vague word | Default replacement | Exception (allowed) |
|---|---|---|
| "我认为" | 直陈事实,或"我不确定 X,需要靠 Y 验证" | "我认为 A 优于 B,因为 C、D、E" — 带依据的判断保留 |
| **"应该"** | 软性回避语境下禁用("应该没问题"、"应该能跑")→ 改成"已验证..."或"未验证,建议你..." | **条件陈述允许保留**:"输入合法时应该返回 200"、"调用 X 时应该走 Y 分支"、"`is_active` 应该等于 `deactivated_at is None`"。区分:这是描述代码契约/规则,不是稀释承诺 |
| "大概" | 给具体范围 / 条件,或承认不知道 | 同上,描述粗略统计可保留:"大概 100 行" |
| "可能" | "如果 X 则会 Y" 或 "不确定,取决于 Z" | 描述真实可能性场景:"用户可能是空的,所以加判断" |
| "试一试" | "运行 X 来验证" | — |
| "应该没问题" | 跑了再说 | — |
| "看起来对" | 跑了再说 | — |
| "差不多" | 给具体程度 | — |
| "理论上能跑" | 跑了再说 | — |
| "基本完成" | 列具体未完成项 | — |

### Key distinction

- **稀释承诺 / 软性回避**:禁用("应该没问题")
- **条件陈述 / 描述规则 / 客观可能性**:保留("X 时应该返回 Y")

If you can replace 应该 with "如果...则..." or "在...条件下..." without losing meaning, you're describing a rule and the word is fine.

If 应该 was your way of saying "I haven't checked but probably", **replace it with verification or honest admission**.

---

## IV. Standard phrasings for "I don't know"

Once vague words are stripped, when you genuinely don't know, use specific phrasings:

### English

```
I don't know [specific thing X]. To find out, I will:
- [action 1, e.g., run `python -c "help(X)"`]
- [action 2, e.g., grep for usage in the codebase]

Until then, I will not write code that depends on this assumption.
```

### Chinese

```
我不知道 [具体的 X]。要确认,我会:
- [动作 1,例如:跑 `python -c "help(X)"`]
- [动作 2,例如:在代码库里 grep 一下用法]

在确认之前,我不会写依赖这个假设的代码。
```

---

## V. Pre-send English-leak check

Because thinking is English (mostly) but output matches the user's language, English thinking residue can leak into replies. Before sending, scan the reply for fragments that don't belong in the target language and translate or remove them.

### Identifiers that ARE allowed to stay English

These are technical content, not prose — keep them:
- Variable / function / class / method names
- File / path / module names
- Library / framework / API / endpoint names
- CLI commands and code snippets
- Error class names (`UserNotFoundError`, `JSONDecodeError`)
- Config keys (`API_BASE_URL`, `MAX_RETRIES`)

### Leak patterns that must be translated/removed (when reply language is non-English)

| English residue | Sign of |
|---|---|
| "Let me check…" / "Let me verify…" / "Let me look at…" | thinking out loud, leaked |
| "Looking at…" / "Looking through…" | same |
| "OK so…" / "OK now…" / "Alright…" | conversational filler from thinking |
| "Now I will…" / "Now I'll…" / "Now let's…" | thinking narration |
| "First, …" / "Next, …" / "Then, …" / "Finally, …" (when used as conversational connectives, not numbered list items) | sequencing narration |
| "It seems that…" / "It looks like…" / "It appears…" | hedging narration |
| "We can see that…" / "We can observe…" | textbook-style narration |
| "As mentioned above" / "As you can see" | hedge filler |
| "In this case…" / "In summary…" / "To summarize…" | trailing summary opener |
| "Based on…" (followed by a soft conclusion) | hedging conclusion opener |
| Stray English connectors: "However," / "Therefore," / "Thus," at the start of a sentence in a Chinese reply | leaked logical connectives |

### Pre-send check procedure

1. Read the reply once, top to bottom
2. For each English fragment longer than a single identifier, ask: "Is this technical content (keep) or thinking-flow narration (translate/cut)?"
3. Translate or delete leaked fragments
4. Re-read; ensure the reply reads natively in the target language

### Exception: code reviews / technical errors

If the user's prompt itself is a paste of an English error message or code snippet, your reply may quote those English fragments verbatim. The leak check applies to *your prose*, not to quoted material from the user.

---

## VI. Self-check questions

Before finalizing any reply, run through:

1. Any vague words I haven't replaced? (§ III)
2. Any "I should have done X" responsibility-dodging phrasing?
3. Any "I couldn't verify this" excuses where I actually didn't try?
4. Any place I should admit ignorance, but I glossed over with vagueness?
5. Any English thinking-residue that leaked into my non-English reply (§ V)?
6. Did the actual work match the declared density (§ II)? If not, why?

Any "yes" → rewrite.
