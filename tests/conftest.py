import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CLIBASEAPP_SRC = REPO_ROOT / "clibaseapp" / "src"

clibaseapp_src = str(CLIBASEAPP_SRC)
if clibaseapp_src not in sys.path:
    sys.path.insert(0, clibaseapp_src)
