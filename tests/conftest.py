import pathlib
import sys

# validate_prior_year.py lives under the tax-prep skill, not on the path.
# tests/ is at the repo root, so parent.parent is the repo root.
REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / ".claude" / "skills" / "tax-prep" / "scripts"
sys.path.insert(0, str(SCRIPTS))
