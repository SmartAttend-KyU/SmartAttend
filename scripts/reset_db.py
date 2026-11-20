from pathlib import Path
import os
import subprocess

ROOT = Path(__file__).resolve().parents[1]
env = os.environ.copy()

subprocess.run(["alembic", "downgrade", "base"], cwd=ROOT / "backend", env=env, check=True)
subprocess.run(["alembic", "upgrade", "head"], cwd=ROOT / "backend", env=env, check=True)
print("Database schema reset and rebuilt from Alembic migrations.")
