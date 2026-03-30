#!/usr/bin/env python3
"""
Initialize the database by running Alembic migrations.
Usage: python scripts/init_db.py
"""

import subprocess
import sys
from pathlib import Path

# Ensure we run from the backend root
BACKEND_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_ROOT))


def run_migrations() -> None:
    print("Running Alembic migrations...")
    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        cwd=str(BACKEND_ROOT),
        capture_output=True,
        text=True,
    )

    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    if result.returncode != 0:
        print("Migration failed.", file=sys.stderr)
        sys.exit(result.returncode)

    print("Migrations completed successfully.")


if __name__ == "__main__":
    run_migrations()
