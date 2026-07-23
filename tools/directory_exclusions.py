from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable, Mapping


# Private maintenance data: this list is never copied into public site output.
EXCLUDED_DIRECTORY_ENTITIES = frozenset(
    {
        "Meditating Monkey Art Emporium",
        "Raton Art Space",
    }
)


def normalize_entity_text(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = text.encode("ascii", "ignore").decode("ascii").casefold().replace("&", " and ")
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text).split())


EXCLUDED_ENTITY_KEYS = frozenset(normalize_entity_text(name) for name in EXCLUDED_DIRECTORY_ENTITIES)
EXCLUDED_ENTITY_COMPACT_KEYS = frozenset(key.replace(" ", "") for key in EXCLUDED_ENTITY_KEYS)


def references_excluded_directory_entity(value: object) -> bool:
    normalized = normalize_entity_text(value)
    if not normalized:
        return False
    padded = f" {normalized} "
    compact = normalized.replace(" ", "")
    return any(f" {key} " in padded for key in EXCLUDED_ENTITY_KEYS) or any(
        key in compact for key in EXCLUDED_ENTITY_COMPACT_KEYS
    )


def row_references_excluded_directory_entity(row: Mapping[str, object]) -> bool:
    for value in row.values():
        if isinstance(value, str) and references_excluded_directory_entity(value):
            return True
        if isinstance(value, Iterable) and not isinstance(value, (str, bytes, Mapping)):
            if any(references_excluded_directory_entity(item) for item in value):
                return True
    return False


def filter_excluded_directory_rows(rows: Iterable[Mapping[str, object]]) -> list[dict]:
    return [dict(row) for row in rows if not row_references_excluded_directory_entity(row)]
