#!/usr/bin/env python3
"""Build a .zip of the skill to upload to the Claude app as a custom skill.

Usage:
    python3 tools/package_app.py [<out.zip>]     (default: ~/Downloads/one-invoices.zip)

The app has no slash commands, so the zip drops the frontmatter keys that only Claude Code reads
(`argument-hint`, `disable-model-invocation`); the model then invokes the skill from its description.
Standard library only.
"""
import re
import sys
import zipfile
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent / "skills" / "one-invoices"
DROP = ("argument-hint:", "disable-model-invocation:")


def app_skill_md(text: str) -> str:
    head, sep, body = text.partition("\n---\n")
    lines = [l for l in head.splitlines() if not l.startswith(DROP)]
    if re.search(r"<[^<>]*>", "\n".join(lines)):  # the app refuses tag-like text in the frontmatter
        raise SystemExit("SKILL.md frontmatter has text like <tag>: the Claude app refuses it")
    return "\n".join(lines) + sep + body


def main(argv: list[str]) -> int:
    out = Path(argv[0]).expanduser() if argv else Path.home() / "Downloads" / "one-invoices.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(SKILL.rglob("*")):
            if f.is_dir() or f.name == ".DS_Store" or "__pycache__" in f.parts:
                continue
            arc = Path("one-invoices") / f.relative_to(SKILL)
            if f.name == "SKILL.md":
                z.writestr(str(arc), app_skill_md(f.read_text(encoding="utf-8")))
            else:
                z.write(f, str(arc))
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
