from app.core.enums import ErrorCode


class DomainError(Exception):
    """Base class for rule violations. Carries a stable code, never an HTTP status."""

    code: ErrorCode

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


class GameFinishedError(DomainError):
    code = ErrorCode.GAME_FINISHED


class GameArchivedError(DomainError):
    code = ErrorCode.GAME_ARCHIVED


class WrongBoardError(DomainError):
    code = ErrorCode.WRONG_BOARD


class CellOccupiedError(DomainError):
    code = ErrorCode.CELL_OCCUPIED


class BoardAlreadyDecidedError(DomainError):
    code = ErrorCode.BOARD_ALREADY_DECIDED


class AlreadyArchivedError(DomainError):
    code = ErrorCode.ALREADY_ARCHIVED


class GameNotFoundError(DomainError):
    code = ErrorCode.GAME_NOT_FOUND
