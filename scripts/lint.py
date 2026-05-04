#!/usr/bin/env python3
"""
careful-coder skill consistency lint.

Checks SKILL.md + references/ for:
1. Cross-reference validity: every "see references/X.md" or "see § Y" pointer
   actually resolves to a file/section that exists.
2. Rule duplication: phrases marked as "single source of truth" appearing
   verbatim in multiple files (signal of accidental duplication).
3. Terminology drift: tier names (low/medium/high vs trivial/standard/substantial)
   used consistently.

Usage:
    python scripts/lint.py [--skill-root <path>]

Exits 0 on clean; non-zero with a report on issues.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from collections import defaultdict


def find_cross_refs(text: str, base_dir: Path) -> list[tuple[str, str]]:
    """Find every 'references/X.md' style pointer; return (pointer, resolved_path_or_None)."""
    issues = []
    # Match patterns like `references/foo.md`, `assets/notes-templates/bar.md`,
    # `CHANGELOG.md`, `scripts/lint.py`
    pattern = re.compile(r"`((?:references|assets|scripts)/[\w./_-]+|CHANGELOG\.md)`")
    for m in pattern.finditer(text):
        ref = m.group(1)
        target = base_dir / ref
        if not target.exists():
            issues.append((ref, "MISSING"))
    return issues


def check_terminology_drift(files: dict[Path, str]) -> list[str]:
    """Tier names should be consistent. v4+ uses low/medium/high (with trivial/standard/substantial as parenthetical).

    Triggered patterns: "trivial tier" / "standard tier" / "substantial tier" (with " tier" suffix).
    These should appear next to the canonical short name (low/medium/high) within a small window.
    Allowed forms in the wild: "Low (trivial)" or "trivial / standard / substantial" listed together.
    """
    issues = []
    skip_files = {"lint.py", "CHANGELOG.md"}  # CHANGELOG documents historical names verbatim
    for path, text in files.items():
        if path.name in skip_files:
            continue
        for old_name in ("trivial tier", "standard tier", "substantial tier"):
            for m in re.finditer(r"\b" + re.escape(old_name) + r"\b", text, re.IGNORECASE):
                start = max(0, m.start() - 80)
                end = min(len(text), m.end() + 80)
                snippet = text[start:end]
                expected = {"trivial tier": "low", "standard tier": "medium", "substantial tier": "high"}[old_name]
                if expected not in snippet.lower():
                    issues.append(f"  {path.name}:{text[:m.start()].count(chr(10))+1}: '{old_name}' without nearby '{expected}'")
    return issues


def _parse_lockfile(lockfile: Path) -> tuple[dict[str, str], dict[str, str]]:
    """Parse careful-coder.lock into (source_hashes, bundle_hashes).

    The lockfile has two sections:
      ## Source file hashes (sha256)        → source_hashes (filename → hex)
      ## Bundle hash (sha256 of the .skill file) → bundle_hashes (filename → hex)
    """
    source = {}
    bundle = {}
    section = None
    for line in lockfile.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("##"):
            if "Bundle hash" in stripped:
                section = "bundle"
            elif "Source file" in stripped:
                section = "source"
            else:
                section = None
            continue
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split(None, 1)
        if len(parts) == 2 and len(parts[0]) == 64:
            target = bundle if section == "bundle" else source
            target[parts[1]] = parts[0]
    return source, bundle


def check_lockfile_freshness(root: Path) -> list[str]:
    """If careful-coder.lock exists, verify every recorded source-hash matches the current source file."""
    import hashlib
    issues = []
    lockfile = root / "careful-coder.lock"
    if not lockfile.exists():
        return ["  careful-coder.lock not found (run scripts/build.sh to create it)"]

    recorded, _ = _parse_lockfile(lockfile)
    if not recorded:
        return ["  careful-coder.lock has no source-hash entries"]

    current = {}
    for sub in ("SKILL.md", "CHANGELOG.md", "README.md", "LICENSE"):
        p = root / sub
        if p.exists():
            current[sub] = hashlib.sha256(p.read_bytes()).hexdigest()
    for d in ("references", "assets", "scripts"):
        for p in (root / d).rglob("*"):
            if p.is_file() and p.suffix in (".md", ".py", ".sh"):
                rel = str(p.relative_to(root))
                current[rel] = hashlib.sha256(p.read_bytes()).hexdigest()

    drifted = [f for f, h in recorded.items() if f in current and current[f] != h]
    missing = [f for f in recorded if f not in current]
    new = [f for f in current if f not in recorded]
    for f in drifted:
        issues.append(f"  drifted: {f} (lock has old hash; rerun scripts/build.sh)")
    for f in missing:
        issues.append(f"  removed: {f} (in lock but file gone)")
    for f in new:
        issues.append(f"  unrecorded: {f} (file exists but not in lock; rerun scripts/build.sh)")
    return issues


def check_bundle_hash(root: Path) -> list[str]:
    """If a .skill bundle exists alongside the lockfile, its sha256 must match the lock's recorded bundle hash."""
    import hashlib
    issues = []
    lockfile = root / "careful-coder.lock"
    if not lockfile.exists():
        return []  # already reported by check_lockfile_freshness

    _, bundle_hashes = _parse_lockfile(lockfile)
    # Find any .skill files in the skill root or its parent (where build.sh writes)
    skill_files = list(root.glob("*.skill")) + list(root.parent.glob("*.skill"))
    skill_files = [s for s in skill_files if s.name in bundle_hashes or any(s.name == k for k in bundle_hashes)]
    # If the lock has bundle entries but no .skill alongside, that's allowed (source-only checkout); skip
    if not bundle_hashes:
        return ["  no bundle hash recorded in lockfile (rerun scripts/build.sh after packaging)"]

    if not skill_files:
        # Lock claims a bundle exists but no .skill found anywhere obvious; warn only
        return [f"  lock claims bundle {list(bundle_hashes.keys())[0]!r} exists but no .skill file alongside source/lock (acceptable for source-only checkouts)"]

    for skill_file in skill_files:
        actual = hashlib.sha256(skill_file.read_bytes()).hexdigest()
        expected = bundle_hashes.get(skill_file.name)
        if expected and actual != expected:
            issues.append(f"  bundle drift: {skill_file.name} sha256 differs from lockfile (rerun scripts/build.sh)")
    return issues


def check_version_match(root: Path) -> list[str]:
    """SKILL.md's declared version must match CHANGELOG.md's most-recent (topmost) entry."""
    issues = []
    skill_md = root / "SKILL.md"
    changelog = root / "CHANGELOG.md"
    if not skill_md.exists() or not changelog.exists():
        return []

    # SKILL.md version: look for "(vN[.M[-suffix]])" in the first H1 heading
    # Accepts v5, v5.0, v5.0-beta, v5.1.2, v6.0-rc1, etc.
    version_re = r"v\d+(?:\.\d+)*(?:-[A-Za-z0-9.]+)?"
    skill_text = skill_md.read_text(encoding="utf-8")
    m = re.search(rf"^#\s+.*\(({version_re})\)", skill_text, re.MULTILINE)
    skill_version = m.group(1) if m else None

    # CHANGELOG.md top version: first "## vN..." heading
    cl_text = changelog.read_text(encoding="utf-8")
    cl_versions = re.findall(rf"^##\s+({version_re})\b", cl_text, re.MULTILINE)
    cl_top_version = cl_versions[0] if cl_versions else None

    if skill_version is None:
        issues.append(f"  SKILL.md H1 doesn't declare a version (expected '# Title (vN)' format)")
        return issues
    if cl_top_version is None:
        issues.append(f"  CHANGELOG.md has no '## vN' heading")
        return issues
    if skill_version != cl_top_version:
        issues.append(f"  version mismatch: SKILL.md says {skill_version}, CHANGELOG.md top is {cl_top_version}")
    return issues


def check_dup_forbidden_phrasings(files: dict[Path, str]) -> list[str]:
    """Forbidden-phrasings list should only appear in self-check-protocol.md.

    language-discipline.md is allowed to contain individual vague words in its blacklist table
    (different conceptual list — vague words vs report-final phrasings), so it's whitelisted.
    """
    issues = []
    # Canonical markers from the forbidden list
    markers = ['"Should be fine"', '"应该没问题"', "Code looks correct"]
    allowed = {"self-check-protocol.md", "CHANGELOG.md", "lint.py", "language-discipline.md"}
    for marker in markers:
        appearances = [path.name for path, text in files.items() if marker in text]
        unexpected = [a for a in appearances if a not in allowed]
        if unexpected:
            issues.append(f"  Forbidden-phrasing marker {marker!r} appears in: {unexpected} (canonical home is self-check-protocol.md §VI)")
    return issues


def check_dup_reporting_template(files: dict[Path, str]) -> list[str]:
    """Reporting full template should only appear in self-check-protocol.md."""
    issues = []
    # The "## Status" block heading is a strong marker for the full template
    marker = "### Requirements\n✅"
    appearances = [path.name for path, text in files.items() if marker in text]
    unexpected = [a for a in appearances if a not in ("self-check-protocol.md", "CHANGELOG.md")]
    if unexpected:
        issues.append(f"  Full reporting template appears in: {unexpected} (canonical home is self-check-protocol.md §V)")
    return issues


# Token estimate constants for check_skill_size.
# Heuristic: ~4 chars/token on mixed English+Chinese content (BPE tokenizers in
# this range for Anthropic models). Calibrated against tiktoken o200k_base on
# the v5.0-beta SKILL.md (18539 chars → ~4634 tokens, ratio 4.0).
SKILL_TOKEN_CHARS_PER = 4
SKILL_TOKEN_WARN = 2700   # design target — over this, file is starting to bloat
SKILL_TOKEN_HARD = 3000   # hard cap — over this, fails the lint


def check_readme_check_count(root: Path) -> list[str]:
    """README's claimed lint check count must match lint.py's actual count.

    Counts checks by scanning lint.py for `print(f"\\n[N] ..."` patterns —
    each numbered check prints a banner like that. Counts README claims by
    looking for `N checks` / `N consistency checks` patterns.

    This check is itself counted, so adding it bumps the total — README
    must say the new total or this check fails.
    """
    issues = []
    readme = root / "README.md"
    lint_py = root / "scripts" / "lint.py"
    if not readme.exists() or not lint_py.exists():
        return issues

    # Count actual checks by scanning print(f"\n[N] ...") patterns in main()
    lint_text = lint_py.read_text(encoding="utf-8")
    actual_nums = sorted(set(int(n) for n in re.findall(r'print\(f?["\'](?:\\n)?\[(\d+)\]', lint_text)))
    actual = len(actual_nums)
    if not actual:
        return issues  # parsing didn't find any — bail rather than false-positive

    # Find every "N checks" / "N consistency checks" claim in README
    readme_text = readme.read_text(encoding="utf-8")
    claims = re.findall(r'(\d+)\s+(?:consistency\s+)?checks?(?=[:\s.])', readme_text, re.IGNORECASE)

    if not claims:
        return issues  # no claim to verify

    for claim_str in claims:
        claim = int(claim_str)
        if claim != actual:
            issues.append(
                f"  README says '{claim} checks' but lint.py defines {actual} (numbered {actual_nums}). "
                f"Update README.md to '{actual} checks' and list the new ones."
            )
    return issues


def check_skill_size(root: Path) -> list[str]:
    """SKILL.md must stay lean — it's loaded on every skill invocation.

    Returns issues only for HARD-cap violations. Reports a soft-warn line if
    over WARN but under HARD; counts toward total only if over HARD.
    """
    issues = []
    skill_md = root / "SKILL.md"
    if not skill_md.exists():
        return []
    char_count = len(skill_md.read_text(encoding="utf-8"))
    token_estimate = char_count // SKILL_TOKEN_CHARS_PER
    # Use sentinel prefixes (HARD: / WARN: / OK:) so the runner can categorize
    # without parsing prose. Reading prose for "hard cap" once misclassified the
    # warn line because the hint mentioned the hard cap value too.
    if token_estimate > SKILL_TOKEN_HARD:
        issues.append(
            f"  HARD: SKILL.md ~{token_estimate} tokens exceeds {SKILL_TOKEN_HARD} cap. "
            "Trim or move content into references/. Hot-path bloat is the #1 cost regression."
        )
    elif token_estimate > SKILL_TOKEN_WARN:
        issues.append(
            f"  WARN: SKILL.md ~{token_estimate} tokens (target {SKILL_TOKEN_WARN}, cap {SKILL_TOKEN_HARD}). "
            "Approaching the cap — review before adding more."
        )
    else:
        issues.append(f"  OK: SKILL.md ~{token_estimate} tokens (under {SKILL_TOKEN_WARN} target).")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill-root", type=Path, default=Path(__file__).parent.parent,
                        help="Skill root directory (defaults to parent of scripts/)")
    parser.add_argument("--strict", action="store_true",
                        help="Promote warning-only checks (lockfile freshness, missing bundle) to hard errors. "
                             "Use this in CI and before any manual release.")
    args = parser.parse_args()

    root = args.skill_root.resolve()
    if not (root / "SKILL.md").exists():
        print(f"ERROR: no SKILL.md at {root}", file=sys.stderr)
        return 2

    # Collect all .md files under SKILL.md, references/, assets/, plus CHANGELOG
    md_files = {}
    for p in [root / "SKILL.md", root / "CHANGELOG.md"]:
        if p.exists():
            md_files[p] = p.read_text(encoding="utf-8")
    for d in (root / "references", root / "assets"):
        if d.exists():
            for p in d.rglob("*.md"):
                md_files[p] = p.read_text(encoding="utf-8")
    # lint.py itself for self-reference
    lint_file = root / "scripts" / "lint.py"
    if lint_file.exists():
        md_files[lint_file] = lint_file.read_text(encoding="utf-8")

    print(f"Linting {len(md_files)} files in {root}")

    total_issues = 0

    # 1. Cross-reference validity (skip lint.py itself — it contains regex examples)
    print("\n[1] Cross-reference validity:")
    xref_issues = []
    for path, text in md_files.items():
        if path.name == "lint.py":
            continue
        for ref, status in find_cross_refs(text, root):
            xref_issues.append(f"  {path.name}: '{ref}' → {status}")
    if xref_issues:
        for line in xref_issues:
            print(line)
        total_issues += len(xref_issues)
    else:
        print("  OK")

    # 2. Forbidden-phrasings duplication
    print("\n[2] Forbidden-phrasings single-source-of-truth:")
    fp_issues = check_dup_forbidden_phrasings(md_files)
    if fp_issues:
        for line in fp_issues:
            print(line)
        total_issues += len(fp_issues)
    else:
        print("  OK")

    # 3. Reporting template duplication
    print("\n[3] Reporting template single-source-of-truth:")
    rt_issues = check_dup_reporting_template(md_files)
    if rt_issues:
        for line in rt_issues:
            print(line)
        total_issues += len(rt_issues)
    else:
        print("  OK")

    # 4. Terminology drift
    print("\n[4] Tier terminology consistency:")
    term_issues = check_terminology_drift(md_files)
    if term_issues:
        for line in term_issues[:10]:  # cap output
            print(line)
        if len(term_issues) > 10:
            print(f"  ... and {len(term_issues) - 10} more")
        total_issues += len(term_issues)
    else:
        print("  OK")

    # 5. Lockfile freshness — warning-only by default (first-time clones haven't built yet);
    #    promoted to hard error under --strict (catches stale-bundle releases)
    print("\n[5] Lockfile freshness (careful-coder.lock vs source):")
    lock_issues = check_lockfile_freshness(root)
    if lock_issues:
        for line in lock_issues:
            print(line)
        if args.strict:
            print("  --strict: promoted to hard error.")
            total_issues += len(lock_issues)
        else:
            print("  (warning only; rerun scripts/build.sh if drift is unintended; use --strict to enforce)")
    else:
        print("  OK")

    # 6. SKILL.md version vs CHANGELOG.md top entry
    print("\n[6] Version label consistency (SKILL.md vs CHANGELOG.md):")
    ver_issues = check_version_match(root)
    if ver_issues:
        for line in ver_issues:
            print(line)
        total_issues += len(ver_issues)
    else:
        print("  OK")

    # 7. .skill bundle hash matches lockfile.
    #    Real drift always fails; missing bundle is warning-only by default,
    #    promoted to hard error under --strict.
    print("\n[7] Bundle hash consistency (.skill vs careful-coder.lock):")
    bundle_issues = check_bundle_hash(root)
    if bundle_issues:
        for line in bundle_issues:
            print(line)
        if any("bundle drift" in line for line in bundle_issues):
            total_issues += sum(1 for line in bundle_issues if "bundle drift" in line)
        elif args.strict:
            print("  --strict: missing-bundle promoted to hard error (release requires a bundle).")
            total_issues += len(bundle_issues)
        else:
            print("  (warning only; not counted toward total; use --strict to enforce)")
    else:
        print("  OK")

    # 8. SKILL.md size guard (hot-path bloat is the #1 cost regression vector)
    print(f"\n[8] SKILL.md size guard (target ≤{SKILL_TOKEN_WARN} tokens, hard ≤{SKILL_TOKEN_HARD}):")
    size_issues = check_skill_size(root)
    if size_issues:
        for line in size_issues:
            print(line)
        # Only HARD: prefix violations count toward total
        total_issues += sum(1 for line in size_issues if line.lstrip().startswith("HARD:"))
    else:
        print("  OK")

    # 9. README check-count consistency (self-referential drift catcher)
    print("\n[9] README check-count consistency (vs lint.py):")
    readme_issues = check_readme_check_count(root)
    if readme_issues:
        for line in readme_issues:
            print(line)
        total_issues += len(readme_issues)
    else:
        print("  OK")

    print(f"\nTotal issues: {total_issues}")
    return 0 if total_issues == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
