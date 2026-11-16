"""Punto de entrada.

    python main.py                         Servidor de desarrollo en http://127.0.0.1:8000
    python main.py --build                 Genera la web estática en dist/ (para GitHub Pages)
    python main.py --build --base-path /mi-repo
                                           Igual, para publicarla en usuario.github.io/mi-repo/
"""

import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def build(out: Path, base_path: str, site_url: str | None) -> None:
    """Pide cada página a la app de FastAPI y la guarda como archivo HTML."""
    from fastapi.testclient import TestClient

    from app.content import DEFAULT_LANGUAGE
    from app.web import all_page_paths, create_app, page_path

    base_path = base_path.rstrip("/")
    client = TestClient(create_app(base_path=base_path, site_url=site_url))

    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(ROOT / "static", out / "static")

    for path in all_page_paths():
        response = client.get(path)
        response.raise_for_status()
        target = out / path.strip("/") / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(response.text, encoding="utf-8")

    for name in ("404.html", "sitemap.xml", "robots.txt"):
        response = client.get(f"/{name}")
        response.raise_for_status()
        (out / name).write_text(response.text, encoding="utf-8")

    # La raíz redirige al idioma por defecto (en un sitio estático no hay redirección de servidor).
    home = f"{base_path}{page_path(DEFAULT_LANGUAGE, '')}"
    (out / "index.html").write_text(
        "<!doctype html><html lang=\"ca\"><head><meta charset=\"utf-8\">"
        f"<meta http-equiv=\"refresh\" content=\"0; url={home}\">"
        f"<link rel=\"canonical\" href=\"{home}\"><title>Alexei Barberà Roca</title></head>"
        f"<body><a href=\"{home}\">Alexei Barberà Roca</a></body></html>",
        encoding="utf-8",
    )
    # Sin esto, GitHub Pages pasa la web por Jekyll y puede ignorar carpetas.
    (out / ".nojekyll").write_text("", encoding="utf-8")
    print(f"Web generada en {out} ({len(all_page_paths())} páginas)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Web de Alexei Barberà Roca")
    parser.add_argument("--build", action="store_true", help="genera la web estática")
    parser.add_argument("--out", default="dist", help="carpeta de salida de --build")
    parser.add_argument("--base-path", default="", help="subcarpeta de publicación, p. ej. /mi-repo")
    parser.add_argument("--site-url", default=None, help="dirección pública de la web")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    if args.build:
        build(ROOT / args.out, args.base_path, args.site_url)
    else:
        import uvicorn
        uvicorn.run("app.web:app", host="127.0.0.1", port=args.port, reload=True)


if __name__ == "__main__":
    main()
