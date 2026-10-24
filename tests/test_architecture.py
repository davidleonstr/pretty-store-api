"""Reglas de arquitectura por capas: api → services → db, con core/constants como base."""
import ast
import pathlib

APP_DIR = pathlib.Path(__file__).resolve().parents[1] / "app"

# Qué paquetes de `app` puede importar cada capa (además de sí misma).
ALLOWED = {
    "api": {"services", "schemas", "core", "db", "constants", "dependencies"},
    "services": {"db", "schemas", "core", "constants"},
    "db": {"core", "constants"},
    "schemas": {"core", "constants"},
    "core": {"constants"},
}

# Qué servicios puede importar cada servicio.
SERVICE_DEPS = {
    "administradores": set(),
    "auth": {"administradores"},
    "media": set(),
    "categorias": set(),
    "horas": set(),
    "clientes": set(),
    "products": {"categorias", "media"},
    "boxes": {"products", "media"},
    "pickups": {"horas"},
    "pricing": {"products", "boxes"},
    "orders": {"products", "boxes", "pickups", "clientes", "pricing"},
}


def _imports(path: pathlib.Path) -> list[str]:
    """Rutas completas importadas; `from app.services import x` cuenta como `app.services.x`."""
    found = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            found += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.append(node.module)
            found += [f"{node.module}.{a.name}" for a in node.names]
    return found


def _files(layer: str):
    return sorted((APP_DIR / layer).rglob("*.py"))


def _rel(path: pathlib.Path) -> str:
    return str(path.relative_to(APP_DIR))


def test_layers_only_import_what_they_are_allowed_to():
    bad = []
    for layer, allowed in ALLOWED.items():
        for py in _files(layer):
            for imp in _imports(py):
                parts = imp.split(".")
                if parts[0] == "app" and len(parts) > 1 and parts[1] != layer and parts[1] not in allowed:
                    bad.append(f"{_rel(py)} → {imp}")
    assert not bad, bad


def test_api_only_uses_the_db_session_never_repositories():
    """Las rutas abren la transacción (`app.db.session`), pero el SQL vive solo en los repositorios."""
    bad = [f"{_rel(p)} → {imp}" for p in _files("api") for imp in _imports(p)
           if imp.startswith("app.db") and not imp.startswith("app.db.session") and imp != "app.db"]
    assert not bad, bad


def test_public_routes_do_not_use_admin_auth():
    bad = [_rel(p) for p in _files("api/public") if "admin_required" in p.read_text(encoding="utf-8")]
    assert not bad, bad


def test_service_dependency_graph_is_respected():
    bad = []
    for py in _files("services"):
        mine = py.stem
        if mine == "__init__":
            continue
        for imp in _imports(py):
            parts = imp.split(".")
            if parts[:2] == ["app", "services"] and len(parts) >= 3 and parts[2] != mine:
                if parts[2] not in SERVICE_DEPS[mine]:
                    bad.append(f"services/{mine}.py → {parts[2]}")
    assert not bad, bad


def test_every_service_is_declared_in_the_graph():
    declared = {p.stem for p in _files("services") if p.stem != "__init__"}
    assert declared == set(SERVICE_DEPS), declared ^ set(SERVICE_DEPS)


def test_layers_do_not_mix_concerns():
    bad = []
    for layer in ("services", "db"):
        for py in _files(layer):
            if "flask" in _imports(py):
                bad.append(f"{_rel(py)} importa flask")
    for py in _files("schemas"):
        if any(imp.startswith("app.db") for imp in _imports(py)):
            bad.append(f"{_rel(py)} accede a la BD")
    for py in _files("api"):
        if "abort(" in py.read_text(encoding="utf-8"):
            bad.append(f"{_rel(py)} usa abort()")
    assert not bad, bad
