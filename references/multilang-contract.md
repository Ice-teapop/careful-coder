# Multi-Language Contract Alignment

Applies when changes span frontend / backend / multiple services, involving multiple languages or repositories. Core goal: **field names, types, paths, and error formats stay consistent across all language sides**, preventing time bombs like "frontend sends `userId`, backend expects `user_id`".

<summary>
Contents:
- § I: source-of-truth priority (OpenAPI > GraphQL > proto > TS interface / Pydantic > JSON Schema > hand-written contract in notes/)
- § II: change patterns — frontend-only / backend-only / both-at-once (most common, recommended order)
- § III: field naming conventions per language (snake_case vs camelCase) + alias-at-boundary recommendation
- § IV: unified error response shape
- § V: self-check additions for multi-language changes
- § VI: 5 typical antipatterns ("frontend will guess backend", "any types now", "tests pass ≠ fits together", etc.)

Read full when: making a frontend ↔ backend contract change; renaming a field used by multiple services; designing a new API; reviewing whether a "looks consistent" change actually is.
Skim sufficient when: single-language change with no contract surface; or you just need the recommended order for sync changes.
</summary>

---

## I. Core principle: if a contract definition exists, treat it as the source of truth

### Source of truth priority

Look for the project's contract in this order:

1. **OpenAPI / Swagger spec** (`.yaml` / `.json`)
2. **GraphQL schema** (`.graphql` / `.gql`)
3. **Protocol Buffers** (`.proto`)
4. **TypeScript interface / Pydantic model** (shared via codegen)
5. **JSON Schema**
6. Other custom schema tools (zod, io-ts, msgspec)

If the project has any of the above → **that's the single source of truth**. Order of changes must be: **change the schema first → change the implementations**. Don't let the two sides "evolve in parallel".

If the project has no contract tool → maintain a hand-written contract section in `notes/project-context.md` (endpoints, params, field names, types) as the project's contract.

---

## II. Typical change patterns

### 2.1 Frontend-only change

Pre-flight checks:
- [ ] Read the corresponding backend API handler; confirm field names and types
- [ ] If there's an OpenAPI spec, trust the spec — don't say "I remember the backend was..."
- [ ] Check whether the frontend has type generation (openapi-typescript / graphql-codegen). If yes, **regenerate types**.

After the change:
- [ ] Run frontend type check (`tsc --noEmit`)
- [ ] Actually call the API once (dev mode real click, or mock test)

### 2.2 Backend-only API change

Pre-flight checks:
- [ ] **Grep all frontend callers** (search for endpoint URL / client SDK method name)
- [ ] If a spec exists, **change the spec first, then the implementation**
- [ ] Assess: is this a breaking change or additive?
  - **Add a field** → usually additive, frontend unaffected
  - **Remove a field** → breaking; frontend gets undefined
  - **Change a field type** → breaking; frontend may crash or display wrong
  - **Rename a field** → breaking; frontend gets nothing
  - **Change endpoint path** → breaking; frontend 404s
- [ ] Breaking change → **must update frontend in sync**, or keep the old field for a deprecation period

After the change:
- [ ] Backend tests pass
- [ ] **Also run frontend type-check / start dev mode** (don't only verify backend)

### 2.3 Simultaneous frontend + backend change (most common)

Most common AND most error-prone. Recommended order:

1. **Change the schema / contract** (spec / proto / shared types)
2. **Run codegen** (regenerate types on both sides)
3. **Change the backend implementation**, run backend tests
4. **Change the frontend implementation**, run frontend tests + type-check
5. **Make a real call** (start dev, actually trigger the interaction)
6. **Update `notes/project-context.md`** with the field convention

**Critical: don't rename a field on the frontend, then rename it on the backend, and assume they line up.** One side must "see" the other, or both must be generated from the same schema.

---

## III. Field naming conventions

Different languages have different idioms:

| Language | Idiom |
|---|---|
| Python | snake_case |
| JavaScript / TypeScript | camelCase |
| Go | PascalCase (exported) / camelCase (unexported) |
| Rust | snake_case |
| JSON over wire | Project decides — usually snake_case or camelCase |

### Recommended approach

- **Pin one wire format** (JSON / Protobuf), document it in the project root README or `notes/project-context.md`
- **Each language's internal code uses its own idiom**, with a conversion at the serialization boundary:
  - Python: Pydantic `Field(alias="...")`
  - TypeScript: `serialize` / `deserialize` functions, or zod transforms
  - Go: struct tag `json:"user_id"`

**Never let naming consistency depend on "both sides remember"** — there must be automatic conversion.

---

## IV. Consistent error format

API error responses are part of the contract. Common pitfalls:

- Backend returns `{"error": "..."}`, frontend expects `{"message": "..."}`
- Backend uses HTTP status code + empty body, frontend expects body with description
- Different endpoints return inconsistent error shapes

### Recommended

Define a **unified error response shape** that all endpoints follow:

```json
{
  "error": {
    "code": "USER_NOT_FOUND",
    "message": "User with ID 123 not found",
    "details": { ... }
  }
}
```

Document in `notes/project-context.md` under "API conventions"; all changes follow.

---

## V. Self-check additions for multi-language changes

In addition to the standard Step 4 self-check, add:

- [ ] All involved language sides ran their respective type-check / lint?
- [ ] Schema / contract definition file updated?
- [ ] Codegen (if any) re-run?
- [ ] At least one true end-to-end call performed?
- [ ] `notes/project-context.md` updated?

---

## VI. Typical antipatterns

### Antipattern 1: "Frontend, I'll guess the backend returns this field"

Wrong. Always Read backend code or the spec. Don't guess.

### Antipattern 2: "Backend has it, frontend just types it as `any` for now"

Wrong. `any` is debt. Either expand the type, or explicitly state "to be defined in next PR after schema lands".

### Antipattern 3: "Both sides changed and tests pass"

Not enough. **One real end-to-end call** is the verification. Frontend with mock data + backend unit tests passing ≠ frontend and backend actually fit together.

### Antipattern 4: "I added a new field; frontend doesn't consume it yet, but that's fine for now"

Wrong. Frontend not consuming = data flow incomplete. Either frontend consumes in sync, or call it out clearly: "pending frontend PR #X".

### Antipattern 5: "I renamed a field and updated everywhere grep matched"

Possible miss. Also check:
- String concatenations (`f"data.{field_name}"`)
- Config files
- Database fields (if the project uses wire format directly as DB columns)
- Documentation / comments
