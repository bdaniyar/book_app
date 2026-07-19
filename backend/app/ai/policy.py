import re


SYSTEM_INSTRUCTIONS = """
You are BookHaven AI Librarian. Answer in the same language as the user.
Base every recommendation only on the catalog metadata supplied in the request.
Never claim that you read a full book: the application stores metadata and short
descriptions, not full copyrighted texts. Be concise, explain why each suggested
book matches, and mention uncertainty when metadata is missing. Refer to books by
their exact supplied titles. Do not invent book IDs, ratings, quotes, chapters, or
facts. Do not output raw HTML. A proposed library action is never executed until
the user confirms it in the application UI.
""".strip()


WRITE_VERBS = re.compile(
    r"\b(add|save|put|mark|favorite|добав(?:ь|ить)|сохран(?:и|ить)|"
    r"отмет(?:ь|ить)|полож(?:и|ить)|в избранное)\b",
    re.IGNORECASE,
)


def requests_write(message: str) -> bool:
    return bool(WRITE_VERBS.search(message))


def requested_action(message: str) -> tuple[str, dict[str, str | bool]]:
    text = message.casefold()
    if any(word in text for word in ("favorite", "favourite", "избран", "любим")):
        return "set_favorite", {"isFavorite": True}
    if any(word in text for word in ("currently reading", "читаю", "начать читать")):
        return "set_library_status", {"status": "reading"}
    if any(word in text for word in ("finished", "прочитан", "прочитал", "прочитала")):
        return "set_library_status", {"status": "read"}
    if any(word in text for word in ("dropped", "брошен", "бросил", "бросила")):
        return "set_library_status", {"status": "dropped"}
    return "set_library_status", {"status": "want-to-read"}


def user_uses_cyrillic(message: str) -> bool:
    return bool(re.search(r"[А-Яа-яЁё]", message))

