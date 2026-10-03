from collections.abc import Iterator

import pytest
from sqlalchemy.orm import Session

from app.core.db import make_engine, make_session_factory
from app.models import Base


@pytest.fixture
def session() -> Iterator[Session]:
    engine = make_engine("sqlite://")
    Base.metadata.create_all(engine)
    with make_session_factory(engine)() as db_session:
        yield db_session
    engine.dispose()
