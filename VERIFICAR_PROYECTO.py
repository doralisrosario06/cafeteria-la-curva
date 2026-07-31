"""Verificación sin iniciar el servidor. Ejecuta: python VERIFICAR_PROYECTO.py"""
from pathlib import Path
import ast, re, sys
ROOT = Path(__file__).resolve().parent
required = ["app.py", "models.py", "database.py", "config.py", "requirements.txt", "render.yaml", "static/manifest.webmanifest", "static/service-worker.js"]
missing = [p for p in required if not (ROOT / p).exists()]
if missing:
    print("FALTAN ARCHIVOS:", ", ".join(missing)); sys.exit(1)
source = (ROOT / "app.py").read_text(encoding="utf-8")
tree = ast.parse(source)
functions = {n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
refs = set()
for template in (ROOT / "templates").glob("*.html"):
    text = template.read_text(encoding="utf-8")
    refs.update(re.findall(r"url_for\(['\"]([^'\"]+)", text))
missing_routes = sorted(refs - functions - {"static"})
if missing_routes:
    print("RUTAS FALTANTES:", ", ".join(missing_routes)); sys.exit(1)
print("OK: sintaxis, archivos y rutas de plantillas verificados.")
