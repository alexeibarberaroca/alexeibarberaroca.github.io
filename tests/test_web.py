import re
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.content import DEFAULT_LANGUAGE, LANGUAGES, load  # noqa: E402
from app.web import all_page_paths, create_app  # noqa: E402
from main import build  # noqa: E402


def shape(node):
    """La estructura de un JSON sin los textos: claves y longitud de las listas."""
    if isinstance(node, dict):
        return {key: shape(value) for key, value in node.items()}
    if isinstance(node, list):
        return [shape(item) for item in node]
    return None


@pytest.mark.parametrize("language", [code for code in LANGUAGES if code != DEFAULT_LANGUAGE])
def test_translations_have_same_structure(language):
    assert shape(load(language)) == shape(load(DEFAULT_LANGUAGE))


@pytest.mark.parametrize("language", LANGUAGES)
def test_slugs_and_links_are_the_same_in_every_language(language):
    reference, other = load(DEFAULT_LANGUAGE), load(language)
    for section, key in (("experience", "jobs"), ("studies", "items")):
        assert [item["slug"] for item in other[section][key]] == \
               [item["slug"] for item in reference[section][key]]
    assert [f["url"] for f in other["cv"]["files"]] == [f["url"] for f in reference["cv"]["files"]]


@pytest.fixture(scope="module")
def client():
    return TestClient(create_app())


@pytest.mark.parametrize("path", all_page_paths())
def test_every_page_renders(client, path):
    response = client.get(path)
    assert response.status_code == 200
    assert "Alexei Barberà Roca" in response.text


def test_root_redirects_to_default_language(client):
    response = client.get("/", follow_redirects=False)
    assert response.status_code in (302, 307)
    assert response.headers["location"] == f"/{DEFAULT_LANGUAGE}/"


def test_unknown_page_is_404(client):
    assert client.get("/ca/no-existeix/").status_code == 404
    assert client.get("/fr/").status_code == 404


def test_known_typos_are_gone(client):
    html = "".join(client.get(path).text for path in all_page_paths())
    for typo in ("SISTEMAS INFOMÀTICS", "MICROINFORMATICS", "l'importància", "En quan a", "de habilitats"):
        assert typo not in html


@pytest.mark.parametrize("base_path", ["", "/web"])
def test_static_build_has_no_broken_internal_links(tmp_path, base_path):
    out = tmp_path / "dist"
    build(out, base_path, "https://example.com")
    assert (out / "index.html").exists() and (out / ".nojekyll").exists()

    for html_file in out.rglob("*.html"):
        for href in re.findall(r'(?:href|src)="(/[^"#]*)', html_file.read_text(encoding="utf-8")):
            assert href.startswith(base_path + "/"), f"{href} en {html_file}"
            relative = href.removeprefix(base_path).lstrip("/")
            target = out / relative
            assert target.is_file() or (target / "index.html").is_file(), f"{href} en {html_file}"
