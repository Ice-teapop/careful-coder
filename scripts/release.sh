#!/usr/bin/env bash
# scripts/release.sh — one-command local release for careful-coder
#
# Usage:
#   ./scripts/release.sh v5.0-beta              # tag + build + push + create release
#   ./scripts/release.sh v5.0-beta --dry-run    # show what would happen, no remote changes
#
# Requires: gh CLI (authenticated), git, python3, bash 4+
#
# What it does, in order:
#   1. Pre-flight checks (clean tree, on main, gh authed, tag doesn't exist yet)
#   2. Run lint (must be 7/7 green)
#   3. Build .skill bundle (regenerates lockfile)
#   4. Verify bundle hash matches lockfile
#   5. Create annotated git tag
#   6. Push commits + tag to origin
#   7. Create GitHub release; upload .skill as asset
#   8. Auto-detect pre-release from tag (any "-" suffix → pre-release)

set -euo pipefail

# ---------- args ----------
if [ $# -lt 1 ]; then
  echo "usage: $0 <tag> [--dry-run]" >&2
  echo "example: $0 v5.0-beta" >&2
  exit 2
fi

TAG="$1"
DRY_RUN=0
[ "${2:-}" = "--dry-run" ] && DRY_RUN=1

# ---------- helpers ----------
say()  { echo "==> $*"; }
warn() { echo "WARN: $*" >&2; }
die()  { echo "ERROR: $*" >&2; exit 1; }
run()  {
  if [ "$DRY_RUN" = "1" ]; then
    echo "[dry-run] $*"
  else
    eval "$@"
  fi
}

# ---------- locate repo root ----------
SKILL_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SKILL_ROOT"

say "Repo root: $SKILL_ROOT"
say "Tag:       $TAG"
[ "$DRY_RUN" = "1" ] && say "Mode:      DRY RUN (no remote changes)"

# ---------- pre-flight checks ----------
say "Pre-flight checks..."

command -v git    >/dev/null || die "git not found"
command -v gh     >/dev/null || die "gh CLI not found — install: brew install gh"
command -v python3 >/dev/null || die "python3 not found"

# Tag must look like vX.Y[.Z][-suffix]
if ! [[ "$TAG" =~ ^v[0-9]+\.[0-9]+(\.[0-9]+)?(-[a-zA-Z0-9.]+)?$ ]]; then
  die "tag '$TAG' does not match vX.Y[.Z][-suffix] (e.g. v5.0-beta, v5.0, v5.1.2, v5.1-rc1)"
fi

# Inside a git repo?
git rev-parse --git-dir >/dev/null 2>&1 || die "not inside a git repo — run 'git init' first"

# Working tree clean?
if [ -n "$(git status --porcelain)" ]; then
  git status --short
  die "working tree not clean — commit or stash first"
fi

# On main?
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$CURRENT_BRANCH" != "main" ]; then
  warn "current branch is '$CURRENT_BRANCH', not 'main'"
  read -rp "continue anyway? [y/N] " ans
  [ "$ans" = "y" ] || [ "$ans" = "Y" ] || die "aborted"
fi

# Tag doesn't exist locally?
if git rev-parse "$TAG" >/dev/null 2>&1; then
  die "tag '$TAG' already exists locally — delete with: git tag -d $TAG"
fi

# Tag doesn't exist on remote?
if git ls-remote --tags origin 2>/dev/null | grep -q "refs/tags/$TAG$"; then
  die "tag '$TAG' already exists on origin — pick a new version"
fi

# gh authenticated?
gh auth status >/dev/null 2>&1 || die "gh not authenticated — run: gh auth login"

# origin remote exists?
git remote get-url origin >/dev/null 2>&1 || die "no 'origin' remote — add one: git remote add origin git@github.com:<user>/<repo>.git"

# CHANGELOG mentions this tag?
if ! grep -q "^## $TAG" CHANGELOG.md 2>/dev/null; then
  warn "CHANGELOG.md does not have a '## $TAG' section — release notes will be sparse"
fi

# RELEASE_NOTES.md present?
NOTES_FILE=""
if [ -f RELEASE_NOTES.md ]; then
  NOTES_FILE="RELEASE_NOTES.md"
  say "Will use RELEASE_NOTES.md for release body"
elif [ -f CHANGELOG.md ]; then
  # Extract just this version's section to a temp file
  TMP_NOTES="$(mktemp -t release-notes.XXXXXX).md"
  awk -v tag="$TAG" '
    $0 ~ "^## " tag { found=1; print; next }
    found && /^## v/ && $0 !~ tag { exit }
    found { print }
  ' CHANGELOG.md > "$TMP_NOTES"
  if [ -s "$TMP_NOTES" ]; then
    NOTES_FILE="$TMP_NOTES"
    say "Extracted release notes from CHANGELOG.md → $TMP_NOTES"
  fi
fi

say "Pre-flight: OK"

# ---------- lint ----------
say "Running lint..."
python3 scripts/lint.py || die "lint failed — fix issues before releasing"

# ---------- build ----------
say "Building .skill bundle..."
if [ "$DRY_RUN" = "1" ]; then
  echo "[dry-run] bash scripts/build.sh"
else
  bash scripts/build.sh
fi

# ---------- locate the bundle ----------
BUNDLE=""
if [ "$DRY_RUN" = "0" ]; then
  BUNDLE=$(ls *.skill 2>/dev/null | head -1 || true)
  [ -n "$BUNDLE" ] || die "no .skill bundle found after build — check build.sh output"
  BUNDLE_HASH=$(sha256sum "$BUNDLE" | awk '{print $1}')
  BUNDLE_SIZE=$(du -h "$BUNDLE" | awk '{print $1}')
  say "Bundle:    $BUNDLE ($BUNDLE_SIZE, sha256 ${BUNDLE_HASH:0:16}...)"

  # ---------- verify bundle hash matches lockfile ----------
  EXPECTED=$(grep -E "[0-9a-f]{64}  $BUNDLE\$" careful-coder.lock 2>/dev/null | awk '{print $1}' || true)
  if [ -n "$EXPECTED" ] && [ "$EXPECTED" != "$BUNDLE_HASH" ]; then
    die "bundle hash drift — lockfile says $EXPECTED, actual is $BUNDLE_HASH"
  fi

  # If lockfile changed (it always does after a build), commit it
  if ! git diff --quiet careful-coder.lock 2>/dev/null; then
    say "Lockfile updated by build — committing..."
    git add careful-coder.lock
    git commit -m "Build artifacts for $TAG

- Regenerated careful-coder.lock with bundle hash $BUNDLE_HASH"
  fi
fi

# ---------- determine pre-release flag ----------
PRERELEASE_FLAG=""
KIND="Stable"
if [[ "$TAG" == *-* ]]; then
  PRERELEASE_FLAG="--prerelease"
  KIND="Pre-release"
fi
say "Release type: $KIND"

# ---------- create tag ----------
TAG_MSG="$TAG — Released $(date +%Y-%m-%d)"
say "Creating annotated tag $TAG..."
run git tag -a "$TAG" -m "'$TAG_MSG'"

# ---------- push ----------
say "Pushing main + tag to origin..."
run git push origin main
run git push origin "$TAG"

# ---------- create release ----------
say "Creating GitHub release..."
if [ "$DRY_RUN" = "1" ]; then
  echo "[dry-run] gh release create $TAG <bundle.skill> --title '$TAG — $KIND' --notes-file ${NOTES_FILE:-CHANGELOG.md} $PRERELEASE_FLAG"
else
  if [ -n "$NOTES_FILE" ]; then
    gh release create "$TAG" "$BUNDLE" \
      --title "$TAG — $KIND" \
      --notes-file "$NOTES_FILE" \
      $PRERELEASE_FLAG
  else
    gh release create "$TAG" "$BUNDLE" \
      --title "$TAG — $KIND" \
      --generate-notes \
      $PRERELEASE_FLAG
  fi
fi

# ---------- verify ----------
if [ "$DRY_RUN" = "0" ]; then
  say "Verifying release..."
  REL_URL=$(gh release view "$TAG" --json url -q '.url')
  say "Released: $REL_URL"
  gh release view "$TAG" --json assets -q '.assets[] | "  asset: \(.name) (\(.size) bytes)"'
fi

say "Done."
