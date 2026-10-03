from __future__ import annotations

import os
import sys
from pathlib import Path

from app.config import settings


def _seed_empty_docker_database() -> None:
    if (
        not settings.SEED_DEMO_DATA
        or settings.DATABASE_URL != "sqlite:////data/suhail.db"
    ):
        return

    database_path = Path("/data/suhail.db")
    if database_path.is_file() and database_path.stat().st_size:
        return

    from app.db import SessionLocal, init_db
    from app.seed import seed

    init_db()
    db = SessionLocal()
    try:
        result = seed(db)
    finally:
        db.close()

    if result["created"]:
        print("Initialized the empty Docker database with demo data.", flush=True)


def main() -> None:
    _seed_empty_docker_database()
    os.execvp(sys.argv[1], sys.argv[1:])


if __name__ == "__main__":
    main()
