from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, "-m", "scripts.seed_demo"], cwd=ROOT / "backend", check=True)
