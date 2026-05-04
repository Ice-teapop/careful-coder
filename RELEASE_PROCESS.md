# Release process

This document is the canonical reference for cutting a `careful-coder` release. Follow it once for each version.

---

## TL;DR — once everything is set up

```bash
./scripts/release.sh v5.0-beta
```

That single command runs lint, builds the `.skill` bundle, tags the commit, pushes to GitHub, and creates a GitHub Release with the bundle attached. Pre-release flag is auto-detected from the tag suffix.

---

## One-time setup (first release only)

### 1. Install tooling

```bash
brew install gh git python@3.11
gh auth login                 # browser OAuth
```

### 2. Initialize the local repo (if not already)

```bash
cd /Users/han/Documents/careful-coder-v5
git init -b main
git add .
git commit -m "Initial public release prep"
```

### 3. Create the GitHub repo

```bash
gh repo create careful-coder --public \
  --description "Tier-aware engineering discipline skill for Claude Code" \
  --source=. --remote=origin --push
```

### 4. Make the release script executable

```bash
chmod +x scripts/release.sh scripts/build.sh
```

### 5. (Optional) Verify CI works

After the first push, the `.github/workflows/lint.yml` workflow should run and pass. Check at `https://github.com/<you>/careful-coder/actions`.

---

## Cutting a release

### A. Confirm CHANGELOG and RELEASE_NOTES are current

- `CHANGELOG.md` should have a top section `## <new-tag> — Released YYYY-MM-DD (current)`.
- `RELEASE_NOTES.md` should describe **this** release (it gets uploaded as the release body verbatim).
- `SKILL.md` H1 should match the new version.
- Lint will catch most drift. **Always use `--strict` before releasing**:
  ```bash
  python3 scripts/lint.py --strict   # required before any manual release; release.sh runs this for you
  ```
  `--strict` promotes lockfile-drift and missing-bundle warnings to hard errors, so you cannot accidentally ship with stale artifacts.

### B. Commit any open work

```bash
git add -A
git commit -m "Prep <tag> — README polish, CHANGELOG entry, RELEASE_NOTES rewrite"
git push origin main
```

The release script refuses to run with a dirty working tree.

### C. Run the release script

```bash
# Dry run first (recommended)
./scripts/release.sh v5.0-beta --dry-run

# For real
./scripts/release.sh v5.0-beta
```

The script does, in order:

1. Pre-flight: tooling present, tree clean, on `main`, tag unused, gh authed, origin set.
2. Lint must be 7/7 green.
3. `scripts/build.sh` regenerates `careful-coder.lock` and packages the `.skill`.
4. Verify the new bundle's sha256 matches the lockfile entry.
5. Commit the regenerated lockfile if it changed.
6. Create annotated git tag.
7. `git push origin main && git push origin <tag>`.
8. `gh release create` with the `.skill` attached, using `RELEASE_NOTES.md` (or the matching CHANGELOG section) as the body.
9. Auto-detect pre-release: any tag with a `-` suffix (`v5.0-beta`, `v5.1-rc1`) is marked `--prerelease`.

### D. Verify

```bash
gh release view v5.0-beta --web
```

Check: title, pre-release badge (if applicable), `.skill` listed in Assets, body matches RELEASE_NOTES.

Sanity-check the asset:

```bash
gh release download v5.0-beta -p '*.skill' -D /tmp/verify
shasum -a 256 /tmp/verify/careful-coder-v5.skill
# Should equal the bundle hash in careful-coder.lock
```

---

## CI alternative (push-tag-only)

If you prefer to skip the local release script: just push the tag, and the `.github/workflows/release.yml` workflow runs lint, builds the `.skill`, and creates the release for you.

```bash
# After your work is committed and pushed:
git tag -a v5.0-beta -m "v5.0-beta — Released $(date +%Y-%m-%d)"
git push origin v5.0-beta
# Watch the workflow run at:  https://github.com/<you>/careful-coder/actions
```

The CI build uses an in-tree minimal packager (vendored in `release.yml`) so it doesn't need access to the host's `~/.claude` install.

---

## Versioning rules

Tags follow `vMAJOR.MINOR[.PATCH][-suffix]`:

| Tag                | Stable? | When to use                               |
| ------------------ | ------- | ----------------------------------------- |
| `v5.0-beta`        | No      | First public Beta. Schema may change.     |
| `v5.0-rc1`         | No      | Beta is feature-frozen, awaiting sign-off |
| `v5.0`             | Yes     | First stable release                      |
| `v5.0.1`           | Yes     | Bug-fix patch on v5.0                     |
| `v5.1`             | Yes     | New features, backward compatible         |
| `v6.0`             | Yes     | Breaking schema change (config migration) |

Lint check `[6]` enforces that `SKILL.md` H1 matches the top `## v…` entry in `CHANGELOG.md`. Bumping the version means updating both.

---

## Rolling back a bad release

If a release ships broken:

```bash
# 1. Mark it as a draft so users can't download
gh release edit v5.0-beta --draft

# 2. Cut a hot-fix
# ... fix ...
./scripts/release.sh v5.0-beta-hotfix1

# 3. When the new release is up, delete the draft
gh release delete v5.0-beta --yes
git push origin :refs/tags/v5.0-beta   # delete the remote tag
git tag -d v5.0-beta                    # delete local
```

Don't reuse a tag — Git tags are supposed to be immutable. Mint a new one (`-hotfix1`, `.1` patch, etc.).

---

## Files this process touches

| File                          | Role                                       |
| ----------------------------- | ------------------------------------------ |
| `SKILL.md`                    | H1 must match the new version              |
| `CHANGELOG.md`                | New `## <tag>` entry on top                |
| `RELEASE_NOTES.md`            | Replaced for each release (uploaded as body) |
| `careful-coder.lock`          | Auto-regenerated by `build.sh`             |
| `careful-coder-v5.skill`      | Built artifact, uploaded as asset, git-ignored |
| `.github/workflows/release.yml` | CI fallback if you push a tag without using the script |
| `scripts/release.sh`          | The one-command local release                |
