# Alexei Barberà Roca · web personal

Mi web profesional y personal, hecha con **Python y FastAPI**. Sustituye a mi antiguo Google Sites.
En catalán, castellano e inglés.

## Estructura

```
main.py              Servidor de desarrollo y generador de la web estática
app/web.py           Aplicación FastAPI (rutas /<idioma>/<página>/)
app/content.py       Carga los textos
content/ca.json      Todos los textos, uno por idioma (ca es el de referencia)
content/es.json
content/en.json
templates/           Plantillas Jinja2
static/              CSS e imágenes
tests/               Tests (pytest)
.github/workflows/   Publicación automática en GitHub Pages
```

Para cambiar un texto basta con editar los JSON de `content/`, sin tocar el código. Los tests
comprueban que los tres idiomas tengan las mismas claves.

## En tu ordenador

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (en macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt

python main.py                  # http://127.0.0.1:8000
pytest -q                       # tests
python main.py --build          # genera la web estática en dist/
```

## Publicarla en GitHub Pages

1. Crea el repositorio y sube el código a la rama `main`.
   Si lo llamas **`alexeibarbera.github.io`**, la web queda en `https://alexeibarbera.github.io/`.
   Con cualquier otro nombre queda en `https://alexeibarbera.github.io/<repositorio>/`.
2. En el repositorio: **Settings → Pages → Source: GitHub Actions**.
3. Cada `git push` a `main` pasa los tests, genera la web y la publica.

GitHub Pages solo sirve archivos estáticos, así que se publica el resultado de `--build`
(FastAPI genera cada página y se guarda como HTML). Si algún día quieres servirla con FastAPI
en un servidor, como relativedevelopers.com:

```bash
uvicorn app.web:app --host 0.0.0.0 --port 8000
```

con la variable `SITE_URL` apuntando a la dirección pública.
