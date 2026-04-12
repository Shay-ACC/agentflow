import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings


def configure_logging() -> None:
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        )
    root_logger.setLevel(logging.INFO)
    logging.getLogger("app").setLevel(logging.INFO)


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()

    application = FastAPI(
        title=settings.project_name,
        version="0.1.0",
        description="Backend foundation for the AgentFlow portfolio project.",
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(api_router)

    @application.get("/", tags=["meta"])
    def read_root() -> dict[str, str]:
        return {
            "name": settings.project_name,
            "environment": settings.project_env,
            "status": "ok",
        }

    return application


app = create_app()
