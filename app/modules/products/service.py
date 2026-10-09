from app.core import db
from app.core.errors import Conflict, NotFound, ValidationError
from app.core.slug import slugify
from app.modules import categorias, media
from app.modules.products import repository as repo

def _attach_photos(conn, rows: list[dict]) -> list[dict]:
    photos = repo.get_photos(conn, [str(r["id"]) for r in rows])
    by_product: dict[str, list[dict]] = {}
    for ph in photos:
        by_product.setdefault(str(ph["product_id"]), []).append(ph)
    for r in rows:
        r["photos"] = by_product.get(str(r["id"]), [])
    return rows

# ---- API pública (2.6) ---------------------------------------------------
def get_by_slugs(slugs: list[str], only_active: bool = True) -> list[dict]:
    with db.connection() as conn:
        return _attach_photos(conn, repo.get_by_slugs(conn, list(slugs), only_active))

def get_by_ids(ids: list[str]) -> list[dict]:
    with db.connection() as conn:
        return _attach_photos(conn, repo.get_by_ids(conn, [str(i) for i in ids]))

def get_stock_map(ids: list[str]) -> dict[str, int]:
    with db.connection() as conn:
        return {str(r["id"]): r["stock"] for r in repo.get_by_ids(conn, [str(i) for i in ids])}

def deduct_stock(conn, qty_by_id: dict[str, int]) -> None:
    ids = sorted(str(i) for i in qty_by_id)
    rows = repo.lock_for_update(conn, ids)
    short = [r["slug"] for r in rows if r["stock"] < qty_by_id[str(r["id"])]]
    if short:
        raise Conflict("out_of_stock", "Algunos productos no tienen stock suficiente", items=short)
    for r in rows:
        repo.set_stock(conn, str(r["id"]), r["stock"] - qty_by_id[str(r["id"])])

def restore_stock(conn, qty_by_id: dict[str, int]) -> None:
    ids = sorted(str(i) for i in qty_by_id)
    for r in repo.lock_for_update(conn, ids):
        repo.set_stock(conn, str(r["id"]), r["stock"] + qty_by_id[str(r["id"])])

# ---- Catálogo público ------------------------------------------------------
def list_public(q: str | None) -> list[dict]:
    with db.connection() as conn:
        rows = repo.list_products(conn, only_active=True, q_slug=slugify(q or "") or None)
        return _attach_photos(conn, rows)

def get_public(slug: str) -> tuple[dict, list[tuple[dict, list[dict], list[dict]]]]:
    """Producto activo + cajas activas que lo contienen: [(box, items, photos)]."""
    with db.connection() as conn:
        row = repo.get_by_slug(conn, slugify(slug), only_active=True)
        if not row:
            raise NotFound("Producto no encontrado")
        _attach_photos(conn, [row])
        boxes = repo.active_boxes_containing(conn, str(row["id"]))
        ids = [str(b["id"]) for b in boxes]
        items = repo.box_items_with_stock(conn, ids)
        photos = repo.box_photos(conn, ids)
    in_boxes = [
        (b,
         [i for i in items if str(i["box_id"]) == str(b["id"])],
         [p for p in photos if str(p["box_id"]) == str(b["id"])])
        for b in boxes
    ]
    return row, in_boxes

def get_availability(slug: str) -> dict:
    with db.connection() as conn:
        row = repo.get_by_slug(conn, slugify(slug), only_active=True)
    if not row:
        raise NotFound("Producto no encontrado")
    return row

# ---- Administración ----------------------------------------------------------
def list_admin(q: str | None, tag: str | None, sold_out: bool | None) -> list[dict]:
    with db.connection() as conn:
        rows = repo.list_products(conn, only_active=False, q_slug=slugify(q or "") or None, tag=tag or None,
                                  sold_out=sold_out)
        return _attach_photos(conn, rows)

def get_admin(product_id: str) -> dict:
    with db.connection() as conn:
        row = repo.get_by_id(conn, product_id)
        if not row:
            raise NotFound("Producto no encontrado")
        return _attach_photos(conn, [row])[0]

def _new_slug(conn, name: str, exclude_id: str | None = None) -> str:
    slug = slugify(name)
    if not slug:
        raise ValidationError({"name": "Escribe un nombre válido"})
    if repo.slug_exists(conn, slug, exclude_id):
        raise Conflict("slug_taken", "Ya existe un producto con un nombre equivalente")
    return slug

def create_product(conn, data: dict) -> dict:
    categorias.ensure_exists(data["categoria_id"])
    image_ids = media.ensure_exist(data["image_ids"])
    slug = _new_slug(conn, data["name"])
    product_id = repo.insert(
        conn, slug, data["name"], data["emoji"], data["price_cents"], data["categoria_id"],
        data["description"], data["stock"], data["is_active"], data["sort_order"],
    )
    repo.set_images(conn, product_id, image_ids)
    return _attach_photos(conn, [repo.get_by_id(conn, product_id)])[0]

def update_product(conn, product_id: str, data: dict) -> dict:
    current = repo.get_by_id(conn, product_id)
    if not current:
        raise NotFound("Producto no encontrado")
    changes = {k: v for k, v in data.items() if k != "image_ids"}
    if "categoria_id" in changes:
        categorias.ensure_exists(changes["categoria_id"])
    if "name" in changes and changes["name"] != current["name"]:
        changes["slug"] = _new_slug(conn, changes["name"], exclude_id=product_id)
    if "image_ids" in data:
        image_ids = media.ensure_exist(data["image_ids"])
    repo.update(conn, product_id, changes)
    if "image_ids" in data:
        repo.set_images(conn, product_id, image_ids)
    return _attach_photos(conn, [repo.get_by_id(conn, product_id)])[0]

def adjust_stock(conn, product_id: str, change: dict) -> dict:
    rows = repo.lock_for_update(conn, [product_id])
    if not rows:
        raise NotFound("Producto no encontrado")
    new_stock = change["stock"] if "stock" in change else rows[0]["stock"] + change["delta"]
    if new_stock < 0:
        raise Conflict("out_of_stock", "El stock no puede quedar por debajo de 0")
    repo.set_stock(conn, product_id, new_stock)
    return _attach_photos(conn, [repo.get_by_id(conn, product_id)])[0]

def delete_product(conn, product_id: str) -> None:
    if not repo.get_by_id(conn, product_id):
        raise NotFound("Producto no encontrado")
    boxes = repo.boxes_using(conn, product_id)
    if boxes:
        raise Conflict(
            "in_use",
            "El producto está en una o más cajas; desactívalo con isActive = false",
            boxes=[{"slug": b["slug"], "name": b["name"]} for b in boxes],
        )
    repo.delete(conn, product_id)
