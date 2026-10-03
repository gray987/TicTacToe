from pathlib import Path

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from sqlalchemy import inspect

from app.core.db import make_engine
from app.models import Base

BACKEND = Path(__file__).resolve().parent.parent


def _config(url: str) -> Config:
    config = Config(str(BACKEND / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", url)
    return config


def test_upgrade_creates_schema_matching_the_models(tmp_path: Path) -> None:
    url = f"sqlite:///{tmp_path / 'm.db'}"
    command.upgrade(_config(url), "head")

    engine = make_engine(url)
    try:
        inspector = inspect(engine)
        assert {"games", "moves"} <= set(inspector.get_table_names())
        unique_columns = [u["column_names"] for u in inspector.get_unique_constraints("moves")]
        assert ["game_id", "board", "cell"] in unique_columns
        with engine.connect() as connection:
            diff = compare_metadata(MigrationContext.configure(connection), Base.metadata)
        assert diff == []
    finally:
        engine.dispose()


def test_downgrade_removes_the_tables(tmp_path: Path) -> None:
    url = f"sqlite:///{tmp_path / 'd.db'}"
    config = _config(url)
    command.upgrade(config, "head")
    command.downgrade(config, "base")

    engine = make_engine(url)
    try:
        assert set(inspect(engine).get_table_names()) <= {"alembic_version"}
    finally:
        engine.dispose()
