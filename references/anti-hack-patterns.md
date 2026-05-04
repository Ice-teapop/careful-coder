# Anti-Hack Patterns — Hardcode Scan + Scope-Creep Prevention + Counterintuitive Logic

This document is the **mandatory scan after writing code**. Used in Step 3 and Step 4.

---

## I. Hardcode scan checklist

After writing, walk through your diff line by line. Any match → fix it.

### 1.1 Network-related

- ❌ Hardcoded URL: `requests.get("https://api.prod.company.com/v1/...")`
  - ✅ Replace with: `requests.get(f"{API_BASE_URL}/v1/...")`, where `API_BASE_URL` comes from config / env
- ❌ Hardcoded IP: `socket.connect(("10.0.0.5", 5432))`
  - ✅ Replace with: read from config / env
- ❌ Hardcoded port
  - ✅ Same

### 1.2 Credentials (high-severity)

- ❌ API key: `headers = {"Authorization": "Bearer sk-xxx..."}`
  - ✅ Replace with: `os.getenv("API_KEY")` or a secrets manager
- ❌ Password / token: `db.connect(password="mypassword")`
  - ✅ Same
- ❌ Pasting private key / certificate content directly into code
  - ✅ Read from file / secrets manager
- ❌ Leaving keys in comments ("# token: sk-xxx for testing")
  - ✅ Delete; clean git history too (`git filter-repo` or rewrite)

**Special note**: Even "test" keys, once committed to git, should be treated as leaked — git history gets archived, mirrored, and scanned by GitHub.

### 1.3 Paths

- ❌ Absolute path: `open("/Users/han/Documents/data.csv")`
  - ✅ Replace with: relative path + `pathlib.Path(__file__).parent`, or read from config
- ❌ Assuming current directory: `open("data.csv")`
  - ✅ Replace with: path relative to script location

### 1.4 Magic values

- ❌ `if elapsed > 86400:` (what is 86400?)
  - ✅ Extract a constant: `SECONDS_PER_DAY = 86400`, with a comment
- ❌ `if status == 7:`
  - ✅ Use an enum: `if status == OrderStatus.SHIPPED:`
- ❌ `data[0:10]` without explaining 10
  - ✅ `MAX_PREVIEW_ITEMS = 10` + comment

### 1.5 Debug residue

- ❌ `if user_id == "test_xxx": skip_validation()`
  - ✅ Delete, or convert to a feature flag / config-driven
- ❌ `print("DEBUG:", data)` scattered throughout
  - ✅ Use a logger, or delete before delivery
- ❌ `# TODO: fix this later` (no explanation of "later")
  - ✅ Either fix now, or write a precise condition: `# TODO(2026-Q3): switch to async after V2 launch`

### 1.6 Commented-out code

- ❌ Large blocks of commented-out old code left in
  - ✅ Delete; git history can recover it

### 1.7 Validation bypass

- ❌ `# temporarily skip validation`
  - ✅ Don't "temporarily". Either fix the validation logic, or explicitly add a config flag with a documented use-case
- ❌ `try: ... except: pass` swallowing all exceptions
  - ✅ Catch specific exception types, log them, or re-raise

---

## II. Scope-creep prevention

### 2.1 What counts as scope creep

User asks for A. You "also" change B — even if B "should be changed".

Common temptations:
- See unidiomatic adjacent code → "let me clean it up"
- See a typo → "let me fix it"
- See an unused import → "let me remove it"
- See an obvious bug unrelated to the task → "let me fix it"
- Want to improve code style → "let me refactor"

### 2.2 Why "just doing it" is wrong

- **Diff confusion**: User reviewing the PR can't tell "which changes are the task vs. drive-by edits"
- **Hidden breakage**: Things you think are "unrelated" may affect call sites you didn't grep
- **Time commitment exceeded**: User expected a 5-minute field rename; you delivered a 50-line diff
- **Bypassing decisions**: Some "looks like it should change" code has historical reasons you don't know

### 2.3 The right move

When you discover an out-of-scope problem, **stop** and call it out separately in the report:

```
Noticed in passing:
- Typo in user_service.py: `activte_user` (line 42)
- auth.py seems to have an unhandled edge case (line 88)
- 3 unused imports under helpers/

These are out of scope for the current task. Want me to handle any of them
**separately**? (We can evaluate each.)
```

Let the user decide whether to expand. **Never expand on your own.**

### 2.4 Exception: inseparable dependencies (narrow test)

If an out-of-scope change is a **prerequisite** for the current task (you literally cannot finish without it), do it — but **explicitly call it out** in the report.

**The narrow test**: a change qualifies as "inseparable" only when **the original task's own tests cannot pass without it**. If the task's tests would still pass without your drive-by change, it's scope creep — even if the drive-by is "obviously correct".

**Pass example** (truly inseparable):

```
Out-of-scope but necessary changes:
- Modified db_helper.py's query() signature (added timeout parameter)
- Reason: current task is "make the report endpoint not time out on large
  result sets"; the test for that endpoint times out without the new param
- Impact: 5 call sites updated in sync
```

**Fail example** (looks necessary, actually scope creep):

```
Task: "Fix JWT decode() so it checks the `exp` claim"

Drive-by additions made (and called out): timing-safe sig comparison,
exception handling for malformed base64.

Strict test result: the original task's test "JWT with past exp must be
rejected" passes with a plain `expected != actual` comparison and no
malformed-input handling. So those drive-bys, while defensible on their
own, do NOT qualify as inseparable.

Lesson: should have either landed the exp-fix alone and filed the timing
+ malformed-input concerns as separate suggestions for the user, OR asked
the user to expand scope first.
```

The fail-example pattern is the most common rationalization. Default to "ask the user to expand scope" when the drive-by is *defensible* but not *required* by the task's own tests.

---

## III. Counterintuitive logic

When writing code (especially in someone else's project), watch for "looks reasonable but actually counterintuitive" patterns:

### 3.1 Silent mutation of shared state

- ❌ A function that looks "read-only" but mutates global state
  ```python
  def get_user(id):
      cache[id] = ...  # side effect!
      return user
  ```
- ✅ Name honestly: `get_or_load_user` / `fetch_and_cache_user`

### 3.2 Implicit ordering dependencies

- ❌ Function A must be called before B, but the code doesn't enforce it
  - ✅ Use types / builder pattern / docs to enforce

### 3.3 Same name, different meaning

- ❌ `userId` is `string` in frontend, `int` in backend, `UUID` in DB; conversions everywhere
  - ✅ Unify the type; convert once at the boundary

### 3.4 Silent error swallowing

- ❌ `try: do_x() except: pass`
- ❌ `result.get("data", []) or DEFAULT` (short-circuit logic causes falsy values to be overridden)

### 3.5 Over-clever one-liners

- ❌ `[*map(lambda x: ..., filter(..., reduce(..., data)))]`
- ✅ Split into multiple meaningful lines, with comments

### 3.6 Misleading names

- ❌ `delete_user()` actually does a soft delete (sets `deleted_at`)
- ✅ Rename to `mark_user_deleted()` or `soft_delete_user()`

### 3.7 Side effects in exception paths

- ❌ Exception handler sends webhooks, writes DB, fires events
- ✅ Keep exception paths minimal — just logging + cleanup

### 3.8 Test code in production

- ❌ `if env == "test": use_mock_payment()`
- ✅ Use dependency injection; production code never even knows mocks exist

---

## IV. Post-write scan action

During every self-check, run this mental checklist:

```
Anti-pattern scan:
1. Hardcoded secrets/URLs/paths/magic numbers? [yes/no, list]
2. Debug residue (prints, TODO without context, commented code)? [yes/no, list]
3. Scope outside Step 1 boundary? [yes/no, justify if yes]
4. Misleading names (function does more/less than name suggests)? [yes/no]
5. Silent error swallowing? [yes/no]
6. Implicit ordering / hidden state mutation? [yes/no]
7. Bypass of validation? [yes/no]

If any yes → fix or explain in report.
```

---

## V. Tools that automate part of this

Some checks can be tool-automated. Recommend adding to the project:

| Check | Tool |
|---|---|
| Hardcoded secrets | `gitleaks`, `trufflehog`, `detect-secrets` |
| Debug print residue | `ruff` rule `T201`, `eslint` rule `no-console` |
| Commented-out code | `eradicate` (Python) |
| Excessive complexity | `radon`, `eslint-plugin-complexity` |
| Unused imports | `ruff`, `eslint` |
| Type consistency | `mypy`, `tsc` |

If the project doesn't have these yet, mention in Step 0: "Recommend adding tool X — it auto-detects this class of issue."
