from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqladmin import Admin
from app.db.session import engine
from app.core.config import settings


from app.api.v1.router import api_router


def create_app() -> FastAPI:
    app = FastAPI(title="book_app")
    origins = [
        origin.strip()
        for origin in settings.FRONTEND_ORIGINS.split(",")
        if origin.strip()
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(api_router, prefix="/api/v1")

    return app


app = create_app()

admin = Admin(app, engine)

# Register sqladmin views
from app.admin import admin as _admin_views  # noqa: F401,E402
