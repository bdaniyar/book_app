from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base without model imports, safe for standalone model imports."""

    pass
