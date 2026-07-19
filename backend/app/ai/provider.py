from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Protocol

import httpx

from app.ai.policy import SYSTEM_INSTRUCTIONS, user_uses_cyrillic
from app.core.config import settings


logger = logging.getLogger(__name__)


class AssistantProvider(Protocol):
    name: str
    model: str

    def generate(
        self,
        *,
        message: str,
        history: list[dict[str, str]],
        books: list[dict[str, Any]],
        profile: dict[str, Any],
    ) -> str: ...


@dataclass
class LocalGroundedProvider:
    """Deterministic fallback that keeps the assistant useful without an API key."""

    name: str = "local"
    model: str = "grounded-catalog"

    def generate(
        self,
        *,
        message: str,
        history: list[dict[str, str]],
        books: list[dict[str, Any]],
        profile: dict[str, Any],
    ) -> str:
        del history
        russian = user_uses_cyrillic(message)
        if not books:
            return (
                "В каталоге не нашлось подходящих книг. Попробуйте убрать один из "
                "фильтров или назвать другой жанр."
                if russian
                else "I could not find a matching catalog book. Try removing a filter or naming another genre."
            )

        intro = (
            "Вот наиболее подходящие варианты из вашего каталога:"
            if russian
            else "These are the best matches from your catalog:"
        )
        lines = [intro]
        favorite_genres = {
            str(item).casefold() for item in profile.get("favoriteGenres", [])
        }
        for index, book in enumerate(books[:5], start=1):
            genres = [str(item) for item in book.get("genres", [])]
            matching = [genre for genre in genres if genre.casefold() in favorite_genres]
            details: list[str] = []
            if book.get("rating") is not None:
                details.append(
                    ("рейтинг" if russian else "rating") + f" {book['rating']}"
                )
            if book.get("pages"):
                details.append(f"{book['pages']} " + ("стр." if russian else "pages"))
            if matching:
                details.append(
                    ("любимый жанр: " if russian else "favorite genre: ")
                    + ", ".join(matching)
                )
            suffix = f" — {', '.join(details)}" if details else ""
            lines.append(f"{index}. **{book['title']}** — {book['author']}{suffix}.")
        lines.append(
            "Рекомендации основаны на метаданных каталога, а не на полном тексте книг."
            if russian
            else "These recommendations use catalog metadata, not the full text of the books."
        )
        return "\n".join(lines)


@dataclass
class OpenAIResponsesProvider:
    api_key: str
    model: str
    base_url: str
    timeout_seconds: float
    max_output_tokens: int
    name: str = "openai"

    def generate(
        self,
        *,
        message: str,
        history: list[dict[str, str]],
        books: list[dict[str, Any]],
        profile: dict[str, Any],
    ) -> str:
        context = {
            "user_message": message,
            "recent_conversation": history[-8:],
            "user_taste": profile,
            "catalog_candidates": books,
        }
        payload = {
            "model": self.model,
            "instructions": SYSTEM_INSTRUCTIONS,
            "input": json.dumps(context, ensure_ascii=False, default=str),
            "max_output_tokens": self.max_output_tokens,
        }
        endpoint = f"{self.base_url.rstrip('/')}/responses"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        with httpx.Client(timeout=self.timeout_seconds) as client:
            for attempt in range(2):
                response = client.post(endpoint, headers=headers, json=payload)
                if response.status_code < 400:
                    return _extract_output_text(response.json())
                if response.status_code not in {429, 500, 502, 503, 504} or attempt == 1:
                    response.raise_for_status()
                time.sleep(0.4)
        raise RuntimeError("The LLM provider returned no response")


def _extract_output_text(payload: dict[str, Any]) -> str:
    direct = payload.get("output_text")
    if isinstance(direct, str) and direct.strip():
        return direct.strip()
    parts: list[str] = []
    for item in payload.get("output") or []:
        if not isinstance(item, dict):
            continue
        for content in item.get("content") or []:
            if not isinstance(content, dict):
                continue
            text = content.get("text")
            if isinstance(text, str) and text.strip():
                parts.append(text.strip())
    if not parts:
        raise RuntimeError("The LLM provider returned an empty response")
    return "\n".join(parts)


def _secret_value(value: Any) -> str | None:
    if value is None:
        return None
    getter = getattr(value, "get_secret_value", None)
    raw = getter() if getter else str(value)
    return raw or None


def get_provider() -> AssistantProvider:
    provider = str(getattr(settings, "AI_PROVIDER", "local")).casefold()
    api_key = _secret_value(getattr(settings, "OPENAI_API_KEY", None))
    if provider == "openai" and api_key:
        return OpenAIResponsesProvider(
            api_key=api_key,
            model=str(getattr(settings, "OPENAI_MODEL", "gpt-5.6-sol")),
            base_url=str(
                getattr(settings, "OPENAI_BASE_URL", "https://api.openai.com/v1")
            ),
            timeout_seconds=float(getattr(settings, "AI_TIMEOUT_SECONDS", 30.0)),
            max_output_tokens=int(getattr(settings, "AI_MAX_OUTPUT_TOKENS", 900)),
        )
    return LocalGroundedProvider()


def provider_status() -> tuple[str, str, bool]:
    provider = get_provider()
    configured = provider.name == "openai"
    return provider.name, provider.model, configured


def generate_with_fallback(**kwargs: Any) -> str:
    provider = get_provider()
    try:
        return provider.generate(**kwargs)
    except (httpx.HTTPError, RuntimeError, ValueError):
        logger.exception("AI provider failed; using grounded local response")
        local_answer = LocalGroundedProvider().generate(**kwargs)
        message = str(kwargs.get("message", ""))
        notice = (
            "Облачная генерация временно недоступна; ниже — локальный подбор по каталогу."
            if user_uses_cyrillic(message)
            else "Hosted generation is temporarily unavailable; below is a local catalog match."
        )
        return f"{notice}\n\n{local_answer}"
