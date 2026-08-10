"""One-off helper: compile CREATE TABLE/TYPE/INDEX DDL for the full schema
against the postgresql dialect using a mock engine (no live DB required).
Used to hand-author the initial Alembic migration when a Postgres instance
is not reachable in the current environment. Not part of the app runtime.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_mock_engine

import app.models  # noqa: F401
from app.core.database import Base

statements: list[str] = []


def dump(sql, *multiparams, **params):
    statements.append(str(sql.compile(dialect=engine.dialect)).strip() + ";")


engine = create_mock_engine("postgresql+psycopg://", dump)
Base.metadata.create_all(engine, checkfirst=False)

output = Path(__file__).resolve().parent / "ddl_output.sql"
output.write_text("\n\n".join(statements), encoding="utf-8")
print(f"Wrote {len(statements)} statements to {output}")
