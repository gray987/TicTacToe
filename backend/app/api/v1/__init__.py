from fastapi import APIRouter

from app.api.v1.games import API_PREFIX
from app.api.v1.games import router as games_router

api_router = APIRouter(prefix=API_PREFIX)
api_router.include_router(games_router)
