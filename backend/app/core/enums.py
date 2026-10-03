from enum import StrEnum


class Player(StrEnum):
    X = "x"
    O = "o"  # noqa: E741


class BoardStatus(StrEnum):
    OPEN = "open"
    X = "x"
    O = "o"  # noqa: E741
    TIED = "tied"


class GameStatus(StrEnum):
    IN_PROGRESS = "in_progress"
    WON = "won"
    DRAWN = "drawn"


class ErrorCode(StrEnum):
    GAME_FINISHED = "game_finished"
    GAME_ARCHIVED = "game_archived"
    WRONG_BOARD = "wrong_board"
    CELL_OCCUPIED = "cell_occupied"
    BOARD_ALREADY_DECIDED = "board_already_decided"
    ALREADY_ARCHIVED = "already_archived"
    GAME_NOT_FOUND = "game_not_found"
    VALIDATION_ERROR = "validation_error"


class GameSort(StrEnum):
    OLDEST = "created_at"
    NEWEST = "-created_at"
