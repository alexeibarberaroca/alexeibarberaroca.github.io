"""Contenido de la web.

Cada idioma es un archivo JSON en content/ con las mismas claves. El catalán (ca) es el
idioma de referencia: si a otro idioma le falta una clave, los tests lo detectan.
Para cambiar un texto de la web basta con editar el JSON; no hace falta tocar el código.
"""

import json
from functools import lru_cache
from pathlib import Path

CONTENT_DIR = Path(__file__).resolve().parent.parent / "content"
DEFAULT_LANGUAGE = "ca"
# Orden en el que aparecen en el selector de idioma.
LANGUAGES = ("es", "ca", "en")


@lru_cache
def load(language: str) -> dict:
    if language not in LANGUAGES:
        raise ValueError(f"Idioma no disponible: {language}")
    path = CONTENT_DIR / f"{language}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def language_names() -> dict[str, str]:
    """Código -> nombre del idioma en su propia lengua, p. ej. {"ca": "Català"}."""
    return {code: load(code)["_meta"]["name"] for code in LANGUAGES}
