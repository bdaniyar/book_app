from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    books,
    genres,
    library,
    profile,
    recommendations,
    reviews,
    search,
    assistant,
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(profile.router)
api_router.include_router(genres.router)
api_router.include_router(books.router)
api_router.include_router(library.router)
api_router.include_router(reviews.router)
api_router.include_router(recommendations.router)
api_router.include_router(search.router)
api_router.include_router(assistant.router)
