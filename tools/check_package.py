#!/usr/bin/env python3
"""Check distributable files, local Markdown links and accidental secret markers."""
from pathlib import Path
import ast
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "visual-story-production"
EXCLUDED = {".git", "__pycache__", ".venv", "dist"}
SECRETS = [
    re.compile(r"(?:gh[pousr]_)[A-Za-z0-9_]{24,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{30,}"),
    re.compile(r"sk-[A-Za-z0-9_-]{24,}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
]
FORBIDDEN_PATHS = {".env", ".github-token", "dev.db", "workbench-v1.db"}


def check(root=ROOT):
    errors = []
    root = Path(root).resolve()
    skill = root / "skills" / "visual-story-production"
    required = [skill / "SKILL.md", skill / "LICENSE.txt", skill / "INSTALL.md",
                skill / "assets" / "project-template" / "project.json", root / "LICENSE"]
    for path in required:
        if not path.is_file():
            errors.append("Missing required file: " + str(path.relative_to(root)))
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if any(part in EXCLUDED for part in rel.parts):
            continue
        if path.is_symlink():
            errors.append("Symlink is not allowed in public package: " + str(rel))
            continue
        if not path.is_file():
            continue
        if path.name in FORBIDDEN_PATHS or path.suffix in (".db", ".sqlite", ".sqlite3"):
            errors.append("Private/runtime file: " + str(rel))
            continue
        if path.suffix not in (".md", ".txt", ".json", ".yaml", ".yml", ".py") and path.name not in ("LICENSE", ".gitignore", ".gitattributes"):
            errors.append("Unexpected public file type: " + str(rel))
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeError, OSError):
            errors.append("Unreadable text file: " + str(rel))
            continue
        for pattern in SECRETS:
            if pattern.search(text):
                # Never print matching content.
                errors.append("Potential secret marker in " + str(rel))
        if path.suffix == ".py":
            try:
                ast.parse(text, filename=str(rel))
            except SyntaxError:
                errors.append("Invalid Python syntax: " + str(rel))
        if path.suffix == ".md":
            for link in re.findall(r"\]\(([^)]+)\)", text):
                if "://" in link or link.startswith("#"):
                    continue
                target = link.split("#", 1)[0]
                resolved = (path.parent / target).resolve()
                if not resolved.is_relative_to(root) or not resolved.exists():
                    errors.append("Broken/escaping local link in " + str(rel) + ": " + target)
    entry = skill / "SKILL.md"
    if entry.is_file():
        text = entry.read_text(encoding="utf-8")
        if not text.startswith("---\nname: visual-story-production\ndescription: "):
            errors.append("Skill frontmatter/name missing")
        if len(text.splitlines()) > 200:
            errors.append("Skill entry should stay concise; move stage detail to references")
        for marker in ("{{", "[TODO", "TODO:"):
            if marker in text:
                errors.append("Unfinished skill scaffold")
    return errors


def main():
    errors = check()
    for error in errors:
        print("ERROR: " + error)
    print("Package checks: " + ("FAIL" if errors else "PASS"))
    print("This scan is a guardrail, not a guarantee of absence of private information.")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
