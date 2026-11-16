"""Aplicación FastAPI.

Las páginas están en /<idioma>/<página>/, por ejemplo /ca/experience/ o /en/studies/.
La raíz (/) lleva al idioma por defecto.

base_path sirve para publicar la web en una subcarpeta (p. ej. GitHub Pages en
usuario.github.io/repositorio/): se antepone a todos los enlaces que genera la web.
site_url es la dirección pública, para los enlaces canónicos y el sitemap.
"""

import os
from datetime import date
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.content import DEFAULT_LANGUAGE, LANGUAGES, language_names, load

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SITE_URL = "https://alexeibarberaroca.github.io"
IMAGE_EXTENSIONS = ("svg", "webp", "png", "jpg", "jpeg")

# Página -> plantilla. "" es la portada.
PAGES = {
    "": "home.html",
    "experience": "experience.html",
    "studies": "studies.html",
    "projects": "projects.html",
    "skills": "skills.html",
}


def page_path(language: str, page: str) -> str:
    return f"/{language}/{page}/" if page else f"/{language}/"


def all_page_paths() -> list[str]:
    return [page_path(language, page) for language in LANGUAGES for page in PAGES]


def create_app(base_path: str = "", site_url: str | None = None) -> FastAPI:
    base_path = base_path.rstrip("/")
    site_url = (site_url or os.environ.get("SITE_URL") or DEFAULT_SITE_URL).rstrip("/")

    app = FastAPI(title="Alexei Barberà Roca", docs_url=None, redoc_url=None, openapi_url=None)
    app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
    templates = Jinja2Templates(directory=ROOT / "templates")

    def url(path: str) -> str:
        """Enlace interno con la subcarpeta de publicación delante."""
        return f"{base_path}{path}"

    def image(name: str) -> str | None:
        """URL de static/img/<name>.<ext> si la imagen existe; si no, None y no se muestra.

        Así basta con dejar el archivo en su carpeta (p. ej. static/img/companies/btech.png)
        para que aparezca en la web, sin tocar plantillas ni JSON.
        """
        for extension in IMAGE_EXTENSIONS:
            relative = f"img/{name}.{extension}"
            if (ROOT / "static" / relative).is_file():
                return url(f"/static/{relative}")
        return None

    templates.env.globals.update(
        url=url,
        image=image,
        page_path=page_path,
        site_url=site_url,
        base_path=base_path,
        languages=language_names(),
        year=date.today().year,
    )

    def render(request: Request, language: str, page: str, status_code: int = 200) -> HTMLResponse:
        text = load(language)
        return templates.TemplateResponse(
            request,
            PAGES.get(page, "404.html"),
            {"t": text, "lang": language, "page": page},
            status_code=status_code,
        )

    @app.get("/", include_in_schema=False)
    def root():
        return RedirectResponse(url(page_path(DEFAULT_LANGUAGE, "")))

    @app.get("/robots.txt", response_class=PlainTextResponse)
    def robots():
        return f"User-agent: *\nAllow: /\nSitemap: {site_url}{url('/sitemap.xml')}\n"

    @app.get("/sitemap.xml")
    def sitemap():
        entries = "".join(
            f"<url><loc>{site_url}{url(path)}</loc></url>" for path in all_page_paths()
        )
        xml = ('<?xml version="1.0" encoding="UTF-8"?>'
               f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{entries}</urlset>')
        return Response(xml, media_type="application/xml")

    @app.get("/404.html", include_in_schema=False)
    def not_found_page(request: Request):
        return render(request, DEFAULT_LANGUAGE, "404", status_code=200)

    @app.get("/{language}/", response_class=HTMLResponse)
    def home(request: Request, language: str):
        return page(request, language, "")

    @app.get("/{language}/{page_name}/", response_class=HTMLResponse)
    def page(request: Request, language: str, page_name: str):
        if language not in LANGUAGES or page_name not in PAGES:
            raise HTTPException(404)
        return render(request, language, page_name)

    @app.exception_handler(404)
    def not_found(request: Request, exc):
        first = request.url.path.removeprefix(base_path).strip("/").split("/")[0]
        language = first if first in LANGUAGES else DEFAULT_LANGUAGE
        return render(request, language, "404", status_code=404)

    return app


app = create_app()
