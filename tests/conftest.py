import pathlib
import sys

# tests/ is at the repo root, so parent.parent is the repo root.
REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# Repo root on the path so `engine` (shared constants) is importable.
sys.path.insert(0, str(REPO_ROOT))

# Skill scripts live under .claude/skills/*/scripts, not on the path.
for _skill in ("tax-prep", "tax-cheatsheet", "tax-audit", "tax-advisor"):
    sys.path.insert(0, str(REPO_ROOT / ".claude" / "skills" / _skill / "scripts"))
