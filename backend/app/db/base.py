from app.db.base_class import Base

# Import models so SQLAlchemy registers them on Base.metadata
from app.models.user import User  # noqa: F401
from app.models.genre import Genre  # noqa: F401
from app.models.user_favorite_genre import user_favorite_genres  # noqa: F401
from app.models.author import Author  # noqa: F401
from app.models.book import Book  # noqa: F401
from app.models.book_genre import book_genres  # noqa: F401
from app.models.review import Review  # noqa: F401
from app.models.user_book import UserBook  # noqa: F401
from app.models.tokens import (  # noqa: F401
    EmailVerificationToken,
    PasswordResetToken,
    RefreshToken,
)
from app.models.assistant import (  # noqa: F401
    AssistantAction,
    AssistantConversation,
    AssistantMessage,
)
