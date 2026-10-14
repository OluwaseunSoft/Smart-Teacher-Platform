from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass


connect_args = (
    {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
)

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def init_db() -> None:
    from app import models  # noqa: F401  (register models)

    Base.metadata.create_all(bind=engine)
    _upgrade_existing_columns()
    _ensure_bootstrap_admin()


def _upgrade_existing_columns() -> None:
    additions = {
        "materials": ("raw_pages", "corrections_locked", "archived"),
        "chunks": ("source_pages",),
        "academic_years": ("user_id",),
        "subjects": ("archived", "academic_year_id"),
        "ai_usage_logs": ("cost_usd",),
    }
    inspector = inspect(engine)
    with engine.begin() as connection:
        for table_name, names in additions.items():
            if not inspector.has_table(table_name):
                continue
            existing = {column["name"] for column in inspector.get_columns(table_name)}
            for name in names:
                if name in existing:
                    continue
                column = Base.metadata.tables[table_name].columns[name]
                sql_type = column.type.compile(dialect=engine.dialect)
                default = ""
                if name in {"archived", "corrections_locked"}:
                    default = " DEFAULT FALSE"
                connection.execute(
                    text(
                        f'ALTER TABLE "{table_name}" ADD COLUMN "{name}" '
                        f"{sql_type}{default}"
                    )
                )


def _ensure_bootstrap_admin() -> None:
    from sqlalchemy import select

    from app.config import settings

    email = settings.DEFAULT_ADMIN_EMAIL.strip().lower()
    password = settings.DEFAULT_ADMIN_PASSWORD
    if not email or not password:
        return

    from app.models import ROLE_ADMIN, User
    from app.security import hash_password

    db = SessionLocal()
    try:
        existing = db.scalar(select(User).where(User.email == email))
        if existing is not None:
            return
        db.add(
            User(
                email=email,
                password_hash=hash_password(password),
                role=ROLE_ADMIN,
                display_name="Administrator",
            )
        )
        db.commit()
    finally:
        db.close()


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
