from app.core import db
from app.core.errors import Conflict, NotFound, ValidationError
from app.modules.categorias import repository as repo

# ---- API pública (2.6) ---------------------------------------------------
def ensure_exists(categoria_id) -> None:
    from app.core.validation import parse_uuid

    uid = parse_uuid(categoria_id)
    with db.connection() as conn:
        if not uid or not repo.exists_id(conn, uid):
            raise ValidationError({"categoriaId": "Elige una categoría válida"})

# ---- Operaciones admin ---------------------------------------------------
def list_categorias() -> list[dict]:
    with db.connection() as conn:
        return repo.list_all(conn)

def create_categoria(conn, nombre: str, sort_order: int) -> dict:
    if repo.exists_nombre(conn, nombre):
        raise Conflict("name_taken", "Ya existe una categoría con ese nombre")
    return repo.insert(conn, nombre, sort_order)

def update_categoria(conn, categoria_id: str, changes: dict) -> dict:
    if not repo.get_by_id(conn, categoria_id):
        raise NotFound("Categoría no encontrada")
    if "nombre" in changes and repo.exists_nombre(conn, changes["nombre"], exclude_id=categoria_id):
        raise Conflict("name_taken", "Ya existe una categoría con ese nombre")
    return repo.update(conn, categoria_id, nombre=changes.get("nombre"), sort_order=changes.get("sort_order"))

def delete_categoria(conn, categoria_id: str) -> None:
    if not repo.get_by_id(conn, categoria_id):
        raise NotFound("Categoría no encontrada")
    if repo.has_products(conn, categoria_id):
        raise Conflict("in_use", "La categoría tiene productos y no se puede eliminar")
    repo.delete(conn, categoria_id)
