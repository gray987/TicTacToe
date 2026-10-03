from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, event
from sqlalchemy.orm import Session

from app.api.deps import get_session
from app.core.config import Settings
from app.core.db import make_engine, make_session_factory
from app.core.enums import ErrorCode, Player
from app.main import create_app
from app.models import Base
from app.services.rules import MovePosition
from tests.helpers import build_game

X = Player.X
API = "/api/v1"


@pytest.fixture
def engine(tmp_path: Path) -> Iterator[Engine]:
    engine = make_engine(f"sqlite:///{tmp_path / 'api.db'}")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def client(engine: Engine) -> TestClient:
    app = create_app(Settings(database_url="sqlite://"))  # lifespan is not run
    factory = make_session_factory(engine)

    def override() -> Iterator[Session]:
        with factory() as session:
            yield session

    app.dependency_overrides[get_session] = override
    return TestClient(app)


def new_game(client: TestClient) -> int:
    response = client.post(f"{API}/games")
    assert response.status_code == 201
    game_id: int = response.json()["id"]
    return game_id


def move(client: TestClient, game_id: int, board: int, cell: int) -> Any:
    return client.post(f"{API}/games/{game_id}/moves", json={"board": board, "cell": cell})


def play_all(client: TestClient, game_id: int, moves: list[MovePosition]) -> None:
    for position in moves:
        assert move(client, game_id, position.board, position.cell).status_code == 201


def won_game(client: TestClient) -> int:
    game_id = new_game(client)
    play_all(client, game_id, build_game([(0, X), (1, X), (2, X)]))
    return game_id


def state(client: TestClient, game_id: int) -> dict[str, Any]:
    body: dict[str, Any] = client.get(f"{API}/games/{game_id}").json()
    return body


def assert_error(response: Any, status: int, code: ErrorCode) -> None:
    assert response.status_code == status
    body = response.json()
    assert body["code"] == code.value
    assert isinstance(body["detail"], str)
    assert set(body) == {"code", "detail"}


# ---- POST /games, GET /games/{id} ---------------------------------------------------------


def test_create_game_returns_201_with_location_and_fresh_state(client: TestClient) -> None:
    response = client.post(f"{API}/games")
    assert response.status_code == 201
    body = response.json()
    assert response.headers["Location"] == f"{API}/games/{body['id']}"
    assert body["status"] == "in_progress"
    assert body["winner"] is None
    assert body["current_player"] == "x"
    assert body["active_board"] is None
    assert body["move_count"] == 0
    assert body["is_archived"] is False
    assert len(body["boards"]) == 9
    for index, board in enumerate(body["boards"]):
        assert board["index"] == index
        assert board["status"] == "open"
        assert board["cells"] == [None] * 9
    assert body["created_at"].endswith(("Z", "+00:00"))


def test_get_game_returns_full_derived_state(client: TestClient) -> None:
    game_id = new_game(client)
    move(client, game_id, 2, 5)
    body = state(client, game_id)
    assert body["id"] == game_id
    assert body["move_count"] == 1
    assert body["current_player"] == "o"
    assert body["active_board"] == 2
    assert body["boards"][2]["cells"][5] == "x"


def test_get_unknown_game_is_404(client: TestClient) -> None:
    assert_error(client.get(f"{API}/games/999"), 404, ErrorCode.GAME_NOT_FOUND)


def test_non_integer_game_id_is_422(client: TestClient) -> None:
    assert_error(client.get(f"{API}/games/abc"), 422, ErrorCode.VALIDATION_ERROR)


# ---- POST /games/{id}/moves ---------------------------------------------------------------


def test_play_move_returns_201_with_location_and_derived_player(client: TestClient) -> None:
    game_id = new_game(client)
    response = move(client, game_id, 4, 7)
    assert response.status_code == 201
    assert response.headers["Location"] == f"{API}/games/{game_id}/moves"
    body = response.json()
    assert (body["game_id"], body["board"], body["cell"]) == (game_id, 4, 7)
    assert (body["player"], body["move_number"]) == ("x", 1)
    assert move(client, game_id, 4, 0).json()["player"] == "o"


@pytest.mark.parametrize("board", range(9))
def test_first_move_is_allowed_in_any_board(client: TestClient, board: int) -> None:
    assert move(client, new_game(client), board, 0).status_code == 201


def test_opponent_is_forced_into_the_same_board_over_http(client: TestClient) -> None:
    game_id = new_game(client)
    assert move(client, game_id, 2, 5).status_code == 201
    assert_error(move(client, game_id, 5, 0), 409, ErrorCode.WRONG_BOARD)
    assert move(client, game_id, 2, 0).status_code == 201
    assert state(client, game_id)["active_board"] == 2


def test_occupied_cell_is_409(client: TestClient) -> None:
    game_id = new_game(client)
    move(client, game_id, 0, 0)
    assert_error(move(client, game_id, 0, 0), 409, ErrorCode.CELL_OCCUPIED)


def test_decided_board_is_409_and_other_boards_are_free(client: TestClient) -> None:
    game_id = new_game(client)
    play_all(client, game_id, build_game([(0, X)]))
    assert state(client, game_id)["active_board"] is None
    assert_error(move(client, game_id, 0, 8), 409, ErrorCode.BOARD_ALREADY_DECIDED)
    assert move(client, game_id, 7, 7).status_code == 201
    assert state(client, game_id)["active_board"] == 7


def test_tied_board_is_decided_too(client: TestClient) -> None:
    game_id = new_game(client)
    play_all(client, game_id, build_game([(0, None)]))
    body = state(client, game_id)
    assert body["boards"][0]["status"] == "tied"
    assert_error(move(client, game_id, 0, 0), 409, ErrorCode.BOARD_ALREADY_DECIDED)


def test_wrong_board_beats_board_already_decided(client: TestClient) -> None:
    game_id = new_game(client)
    play_all(client, game_id, [*build_game([(0, X)]), MovePosition(3, 0)])
    assert_error(move(client, game_id, 0, 8), 409, ErrorCode.WRONG_BOARD)


def test_finished_game_refuses_moves(client: TestClient) -> None:
    game_id = won_game(client)
    body = state(client, game_id)
    assert (body["status"], body["winner"], body["active_board"]) == ("won", "x", None)
    assert_error(move(client, game_id, 5, 0), 409, ErrorCode.GAME_FINISHED)


def test_archived_game_refuses_moves_and_beats_finished(client: TestClient) -> None:
    game_id = won_game(client)
    assert client.post(f"{API}/games/{game_id}/archive").status_code == 200
    assert_error(move(client, game_id, 5, 0), 409, ErrorCode.GAME_ARCHIVED)


def test_move_on_unknown_game_is_404(client: TestClient) -> None:
    assert_error(move(client, 999, 0, 0), 404, ErrorCode.GAME_NOT_FOUND)


@pytest.mark.parametrize(
    "payload",
    [
        {"board": 9, "cell": 0},
        {"board": -1, "cell": 0},
        {"board": 0, "cell": 9},
        {"board": 0, "cell": -1},
        {"board": 0},
        {},
        {"board": "a", "cell": 0},
        {"board": 0, "cell": 0, "player": "x"},
    ],
)
def test_schema_failures_are_422(client: TestClient, payload: dict[str, Any]) -> None:
    game_id = new_game(client)
    response = client.post(f"{API}/games/{game_id}/moves", json=payload)
    assert_error(response, 422, ErrorCode.VALIDATION_ERROR)
    assert state(client, game_id)["move_count"] == 0


def test_full_game_draw_over_http(client: TestClient) -> None:
    game_id = new_game(client)
    play_all(client, game_id, build_game([(board, None) for board in range(9)]))
    body = state(client, game_id)
    assert (body["status"], body["winner"], body["move_count"]) == ("drawn", None, 81)
    assert_error(move(client, game_id, 0, 0), 409, ErrorCode.GAME_FINISHED)


# ---- GET /games/{id}/moves ----------------------------------------------------------------


def test_list_moves_returns_envelope_with_derived_players(client: TestClient) -> None:
    game_id = new_game(client)
    play_all(client, game_id, [MovePosition(1, 1), MovePosition(1, 2), MovePosition(1, 3)])
    body = client.get(f"{API}/games/{game_id}/moves").json()
    assert (body["total"], body["page"], body["page_size"]) == (3, 1, 100)
    assert [(m["board"], m["cell"], m["player"], m["move_number"]) for m in body["items"]] == [
        (1, 1, "x", 1),
        (1, 2, "o", 2),
        (1, 3, "x", 3),
    ]


def test_list_moves_paginates(client: TestClient) -> None:
    game_id = new_game(client)
    play_all(client, game_id, [MovePosition(1, c) for c in range(5)])
    body = client.get(f"{API}/games/{game_id}/moves", params={"page": 2, "page_size": 2}).json()
    assert [m["cell"] for m in body["items"]] == [2, 3]
    assert body["total"] == 5


def test_list_moves_unknown_game_is_404_and_bad_params_are_422(client: TestClient) -> None:
    assert_error(client.get(f"{API}/games/999/moves"), 404, ErrorCode.GAME_NOT_FOUND)
    game_id = new_game(client)
    for params in ({"page": 0}, {"page_size": 0}, {"page_size": 101}):
        response = client.get(f"{API}/games/{game_id}/moves", params=params)
        assert_error(response, 422, ErrorCode.VALIDATION_ERROR)


# ---- POST /games/{id}/archive -------------------------------------------------------------


def test_archive_returns_200_and_hides_the_game_from_the_list(client: TestClient) -> None:
    game_id = new_game(client)
    response = client.post(f"{API}/games/{game_id}/archive")
    assert response.status_code == 200
    assert response.json()["is_archived"] is True
    assert client.get(f"{API}/games").json()["total"] == 0


def test_archived_game_can_still_be_read(client: TestClient) -> None:
    game_id = won_game(client)
    client.post(f"{API}/games/{game_id}/archive")
    assert state(client, game_id)["is_archived"] is True
    assert client.get(f"{API}/games/{game_id}/moves").status_code == 200


def test_archiving_twice_is_409(client: TestClient) -> None:
    game_id = new_game(client)
    client.post(f"{API}/games/{game_id}/archive")
    assert_error(
        client.post(f"{API}/games/{game_id}/archive"), 409, ErrorCode.ALREADY_ARCHIVED
    )


def test_archive_unknown_game_is_404(client: TestClient) -> None:
    assert_error(client.post(f"{API}/games/999/archive"), 404, ErrorCode.GAME_NOT_FOUND)


# ---- GET /games ---------------------------------------------------------------------------


def test_list_defaults_newest_first_with_summary_items(client: TestClient) -> None:
    ids = [new_game(client) for _ in range(3)]
    move(client, ids[0], 0, 0)
    body = client.get(f"{API}/games").json()
    assert (body["total"], body["page"], body["page_size"]) == (3, 1, 25)
    assert [item["id"] for item in body["items"]] == ids[::-1]
    oldest = body["items"][-1]
    assert set(oldest) == {
        "id", "created_at", "status", "winner", "current_player", "move_count",
    }  # fmt: skip
    assert (oldest["status"], oldest["current_player"], oldest["move_count"]) == (
        "in_progress",
        "o",
        1,
    )


def test_list_sort_created_at_is_oldest_first(client: TestClient) -> None:
    ids = [new_game(client) for _ in range(3)]
    body = client.get(f"{API}/games", params={"sort": "created_at"}).json()
    assert [item["id"] for item in body["items"]] == ids
    body = client.get(f"{API}/games", params={"sort": "-created_at"}).json()
    assert [item["id"] for item in body["items"]] == ids[::-1]


def test_list_status_filter_and_total(client: TestClient) -> None:
    in_progress = new_game(client)
    won = won_game(client)
    won_items = client.get(f"{API}/games", params={"status": "won"}).json()
    assert [i["id"] for i in won_items["items"]] == [won]
    assert (won_items["items"][0]["winner"], won_items["total"]) == ("x", 1)
    active = client.get(f"{API}/games", params={"status": "in_progress"}).json()
    assert [i["id"] for i in active["items"]] == [in_progress]
    assert client.get(f"{API}/games", params={"status": "drawn"}).json()["total"] == 0


def test_list_pagination_envelope(client: TestClient) -> None:
    ids = [new_game(client) for _ in range(3)]
    body = client.get(f"{API}/games", params={"page": 2, "page_size": 2}).json()
    assert [i["id"] for i in body["items"]] == [ids[0]]
    assert (body["total"], body["page"], body["page_size"]) == (3, 2, 2)
    past = client.get(f"{API}/games", params={"page": 9, "page_size": 2}).json()
    assert (past["items"], past["total"]) == ([], 3)


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("sort", "name"),
        ("sort", "id"),
        ("status", "bogus"),
        ("page", "0"),
        ("page", "-1"),
        ("page", "abc"),
        ("page_size", "0"),
        ("page_size", "101"),
    ],
)
def test_list_invalid_params_are_422(client: TestClient, name: str, value: str) -> None:
    assert_error(client.get(f"{API}/games", params={name: value}), 422, ErrorCode.VALIDATION_ERROR)


# ---- derived, never stored ----------------------------------------------------------------


def test_derived_fields_are_computed_not_stored(client: TestClient, engine: Engine) -> None:
    game_id = won_game(client)

    statements: list[str] = []

    @event.listens_for(engine, "before_cursor_execute")
    def record(_c: Any, _cur: Any, statement: str, *_rest: Any) -> None:
        statements.append(statement)

    detail = state(client, game_id)
    listing = client.get(f"{API}/games").json()
    moves = client.get(f"{API}/games/{game_id}/moves").json()

    assert detail["status"] == "won" and detail["winner"] == "x"
    assert listing["items"][0]["status"] == "won"
    assert moves["total"] == detail["move_count"]
    assert statements, "reads should have queried the database"
    verbs = ("INSERT", "UPDATE", "DELETE")
    writes = [s for s in statements if s.lstrip().upper().startswith(verbs)]
    assert writes == []


# ---- OpenAPI contract ---------------------------------------------------------------------


def test_openapi_declares_the_error_envelope(client: TestClient) -> None:
    spec = client.get("/openapi.json").json()
    responses = spec["paths"][f"{API}/games/{{game_id}}/moves"]["post"]["responses"]
    for status in ("404", "409", "422"):
        ref = responses[status]["content"]["application/json"]["schema"]["$ref"]
        assert ref.endswith("/ErrorResponse")
    assert "q" not in {
        p["name"] for p in spec["paths"][f"{API}/games"]["get"].get("parameters", [])
    }


def test_health(client: TestClient) -> None:
    assert client.get("/health").json() == {"status": "ok"}
