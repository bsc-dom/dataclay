import uvicorn
from dataclay.restful.settings import settings


def main() -> None:
    uvicorn.run(
        "dataclay.restful.web.application:get_app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.value.lower(),
        factory=True,
    )


if __name__ == "__main__":
    main()
