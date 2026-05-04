# Project Context

> Maintained by careful-coder. Records long-term project-local technical context.
> Loaded by Step 0 (depth varies by task density — see `references/memory-protocol.md` § IV).
>
> **Field markers**:
> - **REQUIRED / 必填** — fill in on first use of careful-coder in this project
> - **OPTIONAL / 可选** — fill in only if applicable
>
> **Example placeholder cleanup**: any block marked `[Example — auto-remove on first real entry]` is removed by the skill the first time a real entry is written nearby.

---

## Project basics — **REQUIRED / 必填**

- **Project type**: (web app / CLI / library / data scripts / etc.)
- **Main language(s)**:
- **Main framework / version**:
- **Package manager**: (pip / poetry / uv / npm / pnpm / yarn / etc.)

---

## Test / lint tooling — **OPTIONAL / 可选**

- **Test framework**:
- **Lint / type-check tools**:

---

## Deployment URLs — **REQUIRED / 必填** (fill the envs you actually use / 填你实际用的)

| Environment | URL | Notes |
|---|---|---|
| dev | | |
| staging | | |
| prod | | |

---

## Key API endpoints — **OPTIONAL / 可选** (be careful when changing / 改这些要看调用方)

[Example — auto-remove on first real entry]
| Endpoint | Method | Purpose | Callers |
|---|---|---|---|
| /api/v1/users | POST | Create user | frontend/UserForm.tsx; admin script |

---

## Field naming conventions — **REQUIRED / 必填**

- **Wire format** (JSON / API transport): snake_case / camelCase / other?
- **Database columns**:
- **Python internal**: snake_case (default)
- **TypeScript internal**: camelCase (default)
- **Conversion layer**: (Pydantic alias / serializer / etc.)

---

## Key environment variables — **OPTIONAL / 可选**

[Example — auto-remove on first real entry]
| Variable | Purpose | Sensitive? | Default |
|---|---|---|---|
| API_BASE_URL | Override API target | no | https://api.dev.example.com |

---

## Team code style / conventions — **OPTIONAL / 可选** (only project-bound; general prefs → host memory)

- Indentation:
- Line length limit:
- String quote style:
- Comment language:
- Commit message style:

---

## Database / storage — **OPTIONAL / 可选**

- **Primary database**:
- **Cache**:
- **Message queue**:
- **Object storage**:

---

## Third-party service dependencies — **OPTIONAL / 可选**

[Example — auto-remove on first real entry]
| Service | Purpose | Credential management |
|---|---|---|
| Stripe | Payments | env var STRIPE_KEY |

---

## Project-specific gotchas — **OPTIONAL / 可选** (project-specific pitfalls / 本项目特定坑)

- 

---

## Write history — **AUTO-APPENDED / 由 skill 自动追加**

(Auto-appended by careful-coder, most recent first)

- [date] [brief description]
