from .auth import LoginRequest, RegisterRequest, AccessTokenResponse, TokenPairResponse
from .user import UserRead
from .profile import ProfileUpdateRequest
from .genre import GenreRead, FavoriteGenresUpdateRequest

__all__ = [
    "LoginRequest",
    "RegisterRequest",
    "AccessTokenResponse",
    "TokenPairResponse",
    "UserRead",
    "ProfileUpdateRequest",
    "GenreRead",
    "FavoriteGenresUpdateRequest",
]
