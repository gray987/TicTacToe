from typing import Annotated

from fastapi import APIRouter, Query, Response

from app.api.deps import GameServiceDep
from app.api.v1.errors import error_responses
from app.core.enums import GameSort, GameStatus
from app.schemas.games import (
    GameDetail,
    GameListEnvelope,
    MoveCreate,
    MoveListEnvelope,
    MoveOut,
)

API_PREFIX = "/api/v1"

router = APIRouter(prefix="/games", tags=["games"])

PageQuery = Annotated[int, Query(ge=1)]
PageSizeQuery = Annotated[int, Query(ge=1, le=100)]


@router.post("", status_code=201)
def create_game(service: GameServiceDep, response: Response) -> GameDetail:
    snapshot = service.create_game()
    response.headers["Location"] = f"{API_PREFIX}/games/{snapshot.id}"
    return GameDetail.from_snapshot(snapshot)


@router.get("", responses=error_responses(422))
def list_games(
    service: GameServiceDep,
    sort: GameSort = GameSort.NEWEST,
    page: PageQuery = 1,
    page_size: PageSizeQuery = 25,
    status: GameStatus | None = None,
) -> GameListEnvelope:
    result = service.list_games(status=status, sort=sort, page=page, page_size=page_size)
    return GameListEnvelope.from_page(result)


@router.get("/{game_id}", responses=error_responses(404, 422))
def get_game(game_id: int, service: GameServiceDep) -> GameDetail:
    return GameDetail.from_snapshot(service.get_game(game_id))


@router.post("/{game_id}/moves", status_code=201, responses=error_responses(404, 409, 422))
def play_move(
    game_id: int,
    body: MoveCreate,
    service: GameServiceDep,
    response: Response,
) -> MoveOut:
    view = service.play_move(game_id, body.board, body.cell)
    response.headers["Location"] = f"{API_PREFIX}/games/{game_id}/moves"
    return MoveOut.from_view(view)


@router.get("/{game_id}/moves", responses=error_responses(404, 422))
def list_moves(
    game_id: int,
    service: GameServiceDep,
    page: PageQuery = 1,
    page_size: PageSizeQuery = 100,
) -> MoveListEnvelope:
    return MoveListEnvelope.from_page(service.list_moves(game_id, page=page, page_size=page_size))


@router.post("/{game_id}/archive", responses=error_responses(404, 409, 422))
def archive_game(game_id: int, service: GameServiceDep) -> GameDetail:
    return GameDetail.from_snapshot(service.archive_game(game_id))
