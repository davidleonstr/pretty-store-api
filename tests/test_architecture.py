"""Revisa las reglas de la sección 2: capas, imports entre módulos y grafo de dependencias."""
import ast
import pathlib

MODULES_DIR = pathlib.Path(__file__).resolve().parents[1] / "app" / "modules"
CORE_DIR = MODULES_DIR.parent / "core"

# Sección 2.5 (auth se importa solo desde routes_admin.py; se valida aparte)
ALLOWED = {
    "administradores": {"core"},
    "auth": {"core", "administradores"},
    "media": {"core"},
    "categorias": {"core"},
    "horas": {"core"},
    "products": {"core", "categorias", "media"},
    "boxes": {"core", "products", "media"},
    "pickups": {"core", "horas"},
    "clientes": {"core"},
    "orders": {"core", "products", "boxes", "pickups", "clientes"},
}

def _imports(path: pathlib.Path) -> list[str]:
    """Rutas completas importadas: 'app.modules.products' / 'app.modules.products.service'..."""
    found = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            found += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module == "app.modules":
                found += [f"app.modules.{a.name}" for a in node.names]
            else:
                found.append(node.module)
    return found

def _module_files():
    for mod_dir in sorted(p for p in MODULES_DIR.iterdir() if p.is_dir() and not p.name.startswith("__")):
        for py in mod_dir.glob("*.py"):
            yield mod_dir.name, py

def test_routes_never_import_repository():
    bad = [f"{m}/{p.name} → {imp}" for m, p in _module_files() if p.name.startswith("routes_")
           for imp in _imports(p) if imp.split(".")[-1] == "repository"]
    assert not bad, bad

def test_modules_only_import_other_modules_by_package():
    bad = []
    for mod, py in _module_files():
        for imp in _imports(py):
            parts = imp.split(".")
            if parts[:2] == ["app", "modules"] and len(parts) > 3 and parts[2] != mod:
                bad.append(f"{mod}/{py.name} → {imp}")
    assert not bad, bad

def test_dependency_graph_is_respected():
    bad = []
    for mod, py in _module_files():
        for imp in _imports(py):
            parts = imp.split(".")
            if parts[:2] == ["app", "modules"] and len(parts) >= 3 and parts[2] != mod:
                other = parts[2]
                if other == "auth" and py.name == "routes_admin.py":
                    continue  # auth solo se importa desde routes_admin.py
                if other not in ALLOWED[mod]:
                    bad.append(f"{mod}/{py.name} → {other}")
    assert not bad, bad

def test_layers_do_not_mix_concerns():
    bad = []
    for mod, py in _module_files():
        src = py.read_text(encoding="utf-8")
        imports = _imports(py)
        if py.name == "service.py" and "flask" in imports:
            bad.append(f"{mod}/service.py importa flask")
        if py.name == "repository.py" and "flask" in imports:
            bad.append(f"{mod}/repository.py importa Flask")
        if py.name == "schemas.py" and "app.core.db" in imports:
            bad.append(f"{mod}/schemas.py accede a la BD")
        if py.name.startswith("routes_") and "abort(" in src:
            bad.append(f"{mod}/{py.name} usa abort()")
    assert not bad, bad

def test_core_does_not_import_modules():
    bad = [f"{p.name} → {imp}" for p in CORE_DIR.glob("*.py") for imp in _imports(p) if imp.startswith("app.modules")]
    assert not bad, bad
