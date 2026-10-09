from app.core import db
from app.core.errors import Conflict, NotFound, ValidationError
from app.core.slug import slugify
from app.modules import media, products
from app.modules.boxes import repository as repo

def _build(conn, rows: list[dict]) -> list[dict]:
    """Agrega items (con producto), fotos y soldOut a cada caja."""
    box_ids = [str(r["id"]) for r in rows]
    items = repo.list_items(conn, box_ids)
    photos = repo.get_photos(conn, box_ids)
    prods = {str(p["id"]): p for p in products.get_by_ids(sorted({str(i["product_id"]) for i in items}))}
    for r in rows:
        bid = str(r["id"])
        r["items"] = []
        for it in items:
            if str(it["box_id"]) != bid:
                continue
            prod = prods.get(str(it["product_id"]))
            if prod is None:
                continue
            r["items"].append({
                "product_id": str(it["product_id"]), "slug": prod["slug"], "qty": it["qty"],
                "stock": prod["stock"], "product": prod,
            })
        r["photos"] = [p for p in photos if str(p["box_id"]) == bid]
        r["sold_out"] = any(i["stock"] < i["qty"] for i in r["items"])
    return rows

# ---- API pública (2.6) ---------------------------------------------------
def get_by_slugs(slugs: list[str], only_active: bool = True) -> list[dict]:
    with db.connection() as conn:
        return _build(conn, repo.get_by_slugs(conn, list(slugs), only_active))

def get_requirements(box_id: str) -> dict[str, int]:
    """{product_id: qty} de los productos actuales de la caja."""
    with db.connection() as conn:
        return {str(i["product_id"]): i["qty"] for i in repo.list_items(conn, [str(box_id)])}

# ---- Catálogo público ------------------------------------------------------
def list_public(q: str | None, tag: str | None) -> list[dict]:
    with db.connection() as conn:
        rows = repo.list_boxes(conn, only_active=True, q_slug=slugify(q or "") or None, tag=tag or None)
        return _build(conn, rows)

def list_tags() -> list[str]:
    with db.connection() as conn:
        return [t["nombre"] for t in repo.list_tipos(conn)]

def get_public(slug: str) -> dict:
    with db.connection() as conn:
        row = repo.get_by_slug(conn, slugify(slug), only_active=True)
        if not row:
            raise NotFound("Caja no encontrada")
        return _build(conn, [row])[0]

def get_availability(slug: str) -> dict:
    box = get_public(slug)
    missing = [
        {"slug": i["slug"], "needed": i["qty"], "stock": i["stock"]}
        for i in box["items"] if i["stock"] < i["qty"]
    ]
    return {"slug": box["slug"], "missing": missing}

# ---- Administración ----------------------------------------------------------
def list_admin() -> list[dict]:
    with db.connection() as conn:
        return _build(conn, repo.list_boxes(conn, only_active=False))

def get_admin(box_id: str) -> dict:
    with db.connection() as conn:
        row = repo.get_by_id(conn, box_id)
        if not row:
            raise NotFound("Caja no encontrada")
        return _build(conn, [row])[0]

def list_tipos() -> list[dict]:
    with db.connection() as conn:
        return repo.list_tipos(conn)

def _validate_items(items: list[dict]) -> None:
    found = products.get_by_ids([i["product_id"] for i in items])
    if len(found) != len(items):
        raise ValidationError({"items": "Alguno de los productos no existe"})

def _new_slug(conn, name: str, exclude_id: str | None = None) -> str:
    slug = slugify(name)
    if not slug:
        raise ValidationError({"name": "Escribe un nombre válido"})
    if repo.slug_exists(conn, slug, exclude_id):
        raise Conflict("slug_taken", "Ya existe una caja con un nombre equivalente")
    return slug

def _check_tipo(conn, tipo_id: int) -> None:
    if not repo.tipo_exists(conn, tipo_id):
        raise ValidationError({"tipoId": "Elige un tipo de caja válido"})

def create_box(conn, data: dict) -> dict:
    _check_tipo(conn, data["tipo_id"])
    _validate_items(data["items"])
    image_ids = media.ensure_exist(data["image_ids"])
    slug = _new_slug(conn, data["name"])
    box_id = repo.insert(conn, slug, data["name"], data["emoji"], data["price_cents"], data["tipo_id"],
                         data["short"], data["description"], data["is_active"], data["sort_order"])
    repo.set_items(conn, box_id, data["items"])
    repo.set_images(conn, box_id, image_ids)
    return _build(conn, [repo.get_by_id(conn, box_id)])[0]

def update_box(conn, box_id: str, data: dict) -> dict:
    current = repo.get_by_id(conn, box_id)
    if not current:
        raise NotFound("Caja no encontrada")
    changes = {k: v for k, v in data.items() if k not in ("items", "image_ids")}
    if "tipo_id" in changes:
        _check_tipo(conn, changes["tipo_id"])
    if "name" in changes and changes["name"] != current["name"]:
        changes["slug"] = _new_slug(conn, changes["name"], exclude_id=box_id)
    if "items" in data:
        _validate_items(data["items"])
    image_ids = media.ensure_exist(data["image_ids"]) if "image_ids" in data else None
    repo.update(conn, box_id, changes)
    if "items" in data:
        repo.set_items(conn, box_id, data["items"])
    if image_ids is not None:
        repo.set_images(conn, box_id, image_ids)
    return _build(conn, [repo.get_by_id(conn, box_id)])[0]

def delete_box(conn, box_id: str) -> None:
    if not repo.get_by_id(conn, box_id):
        raise NotFound("Caja no encontrada")
    repo.delete(conn, box_id)
