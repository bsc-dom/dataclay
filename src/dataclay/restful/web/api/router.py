from fastapi.routing import APIRouter

from dataclay.restful.web.api import echo, monitoring

api_router = APIRouter()
api_router.include_router(monitoring.router)
api_router.include_router(echo.router, prefix="/echo", tags=["echo"])
# api_router.include_router(redis.router, prefix="/redis", tags=["redis"])
