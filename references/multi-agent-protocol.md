# Multi-Agent Orchestration + Three-Way Debate Protocol

This document defines two classes of multi-agent usage:
1. **Parallel task orchestration** (proactively proposed when the task decomposes well)
2. **Three-way debate** (triggered by difficulty criteria, requires user authorization, includes cost estimate + budget tracking + audit log)

The main agent works solo by default. Any multi-agent activation must follow the sequence: **propose → authorize → execute**.

---

## I. Parallel task orchestration

### 1.1 When to proactively propose

The main agent proactively proposes parallel execution when:

- The task decomposes into ≥ 2 **independent** sub-tasks
- The task benefits from multiple review angles (correctness / performance / security)

### 1.2 Proposal phrasing (specific, not vague)

Wrong:
> "Want me to do this in parallel?"

Right (concretely state how it decomposes):
> "This task decomposes into three independent pieces: (A) modify the frontend LoginForm component, (B) modify the backend /auth/login route, (C) add an e2e test. Want me to spawn 3 sub-agents in parallel? Should save roughly [time estimate]."

### 1.3 How to derive each sub-agent's "do NOT touch" boundary

Open-ended boundaries ("do not touch unrelated code") are useless — sub-agents can't act on them.

Procedure:
1. Grep the current task for the smallest set of directories / modules it logically needs (e.g., for "fix login button styling" → `src/auth/components/LoginForm.tsx` + its CSS module)
2. List those as the **scope**
3. List **everything else** — by directory, with concrete examples — as do-not-touch:
   ```
   Scope (you may modify):
   - src/auth/components/LoginForm.tsx
   - src/auth/styles/login.module.css

   Do NOT touch:
   - tests/ (not your responsibility)
   - scripts/, docs/, README.md
   - any module outside src/auth/
   - the api routes (separate sub-agent owns those)
   ```
4. If a sub-agent finds it must touch something out of scope to complete its task, it stops and reports back to the main agent for arbitration

### 1.4 Main agent's coordination duties (after user agrees)

1. **Distribute context**: Prepare an independent context package for each sub-agent containing:
   - The specific goal of that sub-task
   - Necessary project background (relevant excerpts from notes/)
   - The exact tools the sub-task needs
   - Boundary (per § 1.3)
2. **Don't dump full conversation history**: Give each sub-agent only what it needs. Avoid context pollution.
3. **Collect results**: After each sub-agent reports, the main agent checks:
   - Did it complete the assigned sub-task?
   - Did it cross boundaries?
   - Are there contradictions between sub-agents?
4. **Arbitrate conflicts**: When there are contradictions → main agent decides which side wins (based on conventions in `notes/project-context.md`), or runs another round to align.
5. **Unified reporting**: Merge all sub-agent results into one user-readable report. **Don't make the user assemble it themselves.**

---

## II. Three-way debate protocol

### 2.1 Trigger and proposal (with cost estimate)

Trigger conditions: see `difficulty-criteria.md` (all three of (a)/(b)/(c) hold).

Proposal phrasing **must include a concrete cost estimate**:

> The current task is to implement [specific function], which involves [specific technical concern — e.g., "asyncio task cancellation semantics" / "JWT signature verification"]. This category historically has a high error rate, and a mistake would affect [specific user-visible feature].
>
> Want me to start a **three-way debate**? The flow:
> - I spawn 3 sub-agents; each independently analyzes the implementation
> - When done, they debate to find each other's gaps
> - I supervise as the main agent (preventing off-topic drift, catching hallucinations); the final implementation is based on the consensus
>
> **Cost estimate**: 3 sub-agents × ~2 rounds = roughly **6× single-agent token cost**. For this task that's approximately **[N tokens / $X]** based on the current task length and your model's pricing. Solo cost would be ~[M tokens].
>
> **Your debate budget this month**: [used / remaining] (configurable in `.careful-coder/config.json`).

### 2.2 Cost estimation method

Estimate single-agent cost as a baseline (rough heuristic):
- Read current task description tokens
- Estimate tool-use exchanges needed (each ~500-2000 tokens)
- Sum to baseline

Multiply by ~6× for the 3 × 2-round debate. Then apply user's model pricing if known. Round to nearest dollar (or yuan / your local currency); err on the high side to avoid surprises.

### 2.3 Debate budget

Stored in `.careful-coder/config.json` (schema `version: 1`):
```json
{
  "version": 1,
  "commit_to_git": true,
  "debate_budget_per_month": 5,
  "debates_used_this_month": 2,
  "last_reset_month": "2026-05"
}
```

#### Monthly reset (Step 0 handles)

The reset is **not automatic on the 1st of the month** — there's no cron in this skill. Instead, every Step 0 reads `config.json` and:

1. If current month string > `last_reset_month`:
   - Set `debates_used_this_month = 0`
   - Set `last_reset_month` to current month
   - Write config back

This piggybacks on the user's normal usage: the first careful-coder invocation in a new month does the reset.

#### Budget hit behavior

When proposing, if `debates_used_this_month >= debate_budget_per_month`:
- **Don't bother the user with the proposal** (no question asked).
- After the task is done, mention **once** in the final report: "Budget hit (used X/X this month). I would have proposed three-way debate at [point]; consider raising `debate_budget_per_month` in `.careful-coder/config.json` if you want this for the rest of the month."

This gives the user the audit trail without interrupting the task with a proposal that's already been answered.

If `debate_budget_per_month` is `null`, no budget cap is enforced — propose normally.

### 2.4 Audit log

Each accepted debate appends a row to `.careful-coder/_debate-log.md` (auto-created at first use; **outside** notes/ so it does not consume notes/'s 1500-line size budget):

```markdown
## [YYYY-MM-DD HH:MM] Three-way debate

- **Task**: [brief description]
- **Reason**: [hard-difficulty criterion that triggered]
- **Cost (estimated → actual)**: ~$X estimated → $Y actual
- **Outcome**: [consensus reached / split arbitration / fallback to solo]
```

The log is passive — record what happened, no required user input. (Earlier drafts had a "user verdict" field; removed in v5 because the skill never had a clean way to collect it, so the field was always N/A.)

### 2.5 When user declines

Solo execution proceeds, but **with extra vigilance** noted in thinking (English):
```
Note: user declined three-way debate for [point].
I will be extra careful here:
- Verify each API call individually
- Run the relevant code path explicitly after writing
- Cross-check against [specific known gotcha]
```

### 2.6 Execution flow when user agrees

#### Phase 1: Independent analysis

Spawn 3 sub-agents, each receiving **identical** input:
- Specific task description
- Relevant code
- Necessary project context (extracted from notes/)
- Tool set
- Boundary (per § 1.3)

Each agent independently produces:
- **Approach description** (concrete code or pseudocode)
- **Risk points** (where it thinks this approach might fail)
- **Confidence** (specifically described — not "high/medium/low")

**Don't let agents see each other's approaches** (avoid anchoring).

#### Phase 2: Debate

Main agent assembles the 3 approaches and starts the debate phase:
- Send all 3 approaches + risk points to each agent
- Each agent comments on the other two: agree / disagree / propose modification
- Each agent must give **specific, evidence-based pushback** — not "I just feel A is better"

Debate runs for at most 2 rounds. If no consensus → Phase 3 split arbitration.

#### Phase 3: Consensus or arbitration

- **Consensus reached** → main agent adopts the consensus
- **Split arbitration** → main agent presents all approaches + debate summary to the user; user decides

### 2.7 Main agent's supervision duties

- **Prevent off-topic drift**: any agent drifting → pull back
- **Catch hallucinations**: any cited non-existent API → flag and demand verification
- **Prevent dialogue collapse**: stay focused on facts
- **Cap cost**: ≤ 2 rounds, ≤ 3 exchanges per round

### 2.8 Post-debate handling

Once the consensus approach is known, **don't deliver immediately** — return to the normal discipline (Step 3 write + verify + Step 4 self-check). Debate finds an approach; it doesn't replace verification.

---

## III. Sub-agent input template

```
You are a sub-agent of careful-coder. Your task:

[task description, very specific]

Project context (relevant excerpts only):
[paste relevant parts from notes/project-context.md]

Scope (you may modify):
- [explicit file/directory list]

Do NOT touch:
- [explicit list per § 1.3]

Tools available:
[explicit list]

Constraints:
- Follow the careful-coder discipline (apply density × steps decision table)
- Internal thinking in English (or project language if non-English-dominant)
- Output language: [match user's]
- No vague language ("I think", "should work", "maybe")

Deliverable:
[exact format expected]
```

---

## IV. Cost-control principles

multi-agent isn't cheap. Follow these to avoid abuse:

- **Default solo**. Activation is the exception, not the rule.
- **Strict trigger conditions for three-way debate** (§ 2.1) + budget cap (§ 2.3) + cost estimate in proposal (§ 2.1).
- **Cap debate rounds** (§ 2.7). Don't loop forever.
- **Audit log** (§ 2.4). Periodically review whether debate is paying off.
- **Failure degrades to solo** (§ 2.7). If sub-agents loop or produce noise → halt and ask user.
