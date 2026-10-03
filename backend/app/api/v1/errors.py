from typing import Any, cast

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.enums import ErrorCode
from app.schemas.common import ErrorResponse
from app.services.errors import DomainError

STATUS_BY_CODE: dict[ErrorCode, int] = {
    ErrorCode.GAME_NOT_FOUND: 404,
    ErrorCode.VALIDATION_ERROR: 422,
    ErrorCode.GAME_FINISHED: 409,
    ErrorCode.GAME_ARCHIVED: 409,
    ErrorCode.WRONG_BOARD: 409,
    ErrorCode.CELL_OCCUPIED: 409,
    ErrorCode.BOARD_ALREADY_DECIDED: 409,
    ErrorCode.ALREADY_ARCHIVED: 409,
}

_DESCRIPTIONS = {404: "Game not found", 409: "Rule conflict", 422: "Invalid request"}


def error_responses(*statuses: int) -> dict[int | str, dict[str, Any]]:
    """OpenAPI `responses` entries so generated client types include the error envelope."""
    return {s: {"model": ErrorResponse, "description": _DESCRIPTIONS[s]} for s in statuses}


def _envelope(code: ErrorCode, detail: str) -> JSONResponse:
    body = ErrorResponse(code=code, detail=detail).model_dump(mode="json")
    return JSONResponse(status_code=STATUS_BY_CODE[code], content=body)


async def _domain_error_handler(_: Request, exc: Exception) -> JSONResponse:
    error = cast(DomainError, exc)
    return _envelope(error.code, error.detail)


async def _validation_error_handler(_: Request, exc: Exception) -> JSONResponse:
    errors = cast(RequestValidationError, exc).errors()
    detail = "; ".join(
        f"{'.'.join(str(part) for part in err['loc'])}: {err['msg']}" for err in errors
    )
    return _envelope(ErrorCode.VALIDATION_ERROR, detail)


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DomainError, _domain_error_handler)
    app.add_exception_handler(RequestValidationError, _validation_error_handler)
