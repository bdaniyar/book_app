import re
import uuid

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.session import get_db

_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,128}$")


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

    @app.middleware("http")
    async def security_headers_and_request_id(request: Request, call_next):
        supplied_request_id = request.headers.get("x-request-id", "")
        request_id = (
            supplied_request_id
            if _REQUEST_ID_PATTERN.fullmatch(supplied_request_id)
            else str(uuid.uuid4())
        )
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=()"
        )
        if request.url.path.startswith("/api/v1/auth"):
            response.headers.setdefault("Cache-Control", "no-store")
        if settings.APP_ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        return response

    @app.get("/health")
    @app.get("/health/live")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/health/ready")
    def readiness(db: Session = Depends(get_db)) -> dict[str, str]:
        try:
            db.execute(text("SELECT 1"))
        except SQLAlchemyError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database is unavailable",
            ) from None
        return {"status": "ready"}

    app.include_router(api_router, prefix="/api/v1")

    if settings.ADMIN_ENABLED:
        from app.admin.admin import configure_admin

        configure_admin(app)

    return app


app = create_app()
