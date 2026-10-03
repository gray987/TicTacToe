from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session, sessionmaker

from app.repositories.games import GameRepository
from app.services.games import GameService


def get_session(request: Request) -> Iterator[Session]:
    factory: sessionmaker[Session] = request.app.state.session_factory
    with factory() as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


def get_game_service(session: SessionDep) -> GameService:
    return GameService(GameRepository(session))


GameServiceDep = Annotated[GameService, Depends(get_game_service)]
