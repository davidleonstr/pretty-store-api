"""Resolución de líneas y total del pedido (siempre desde la BD) y regla del mínimo de $3.00."""
from app.core.errors import ValidationError
from app.modules import boxes, products

MIN_PRODUCTS_TOTAL_CENTS = 300
MSG_MIN_TOTAL = "Los pedidos de productos sueltos deben sumar al menos $3.00"

def resolve(kind: str, items: list[dict]) -> dict:
    """Devuelve {lines, total_cents, stock_needs}.

    lines: [{product_id, box_id, name, unit_price_cents, qty}]
    stock_needs: {product_id: qty} a descontar (para una caja, el contenido de la caja).
    Lanza ValidationError con el campo correspondiente.
    """
    if kind == "caja":
        return _resolve_box(items)
    return _resolve_products(items)

def _resolve_box(items: list[dict]) -> dict:
    if len(items) != 1 or items[0]["qty"] != 1:
        raise ValidationError({"items": "Elige una sola caja"})
    found = boxes.get_by_slugs([items[0]["slug"]], only_active=True)
    if not found:
        raise ValidationError({"items": "La caja no existe o no está disponible"})
    box = found[0]
    stock_needs: dict[str, int] = {}
    for it in box["items"]:
        stock_needs[it["product_id"]] = stock_needs.get(it["product_id"], 0) + it["qty"]
    return {
        "lines": [{"product_id": None, "box_id": str(box["id"]), "name": box["name"],
                   "unit_price_cents": box["price_cents"], "qty": 1}],
        "total_cents": box["price_cents"],
        "stock_needs": stock_needs,
    }

def _resolve_products(items: list[dict]) -> dict:
    merged: dict[str, int] = {}
    for it in items:  # los repetidos se suman
        merged[it["slug"]] = merged.get(it["slug"], 0) + it["qty"]
    found = {p["slug"]: p for p in products.get_by_slugs(list(merged), only_active=True)}
    if len(found) != len(merged):
        raise ValidationError({"items": "Alguno de los productos no existe o no está disponible"})
    lines, total, needs = [], 0, {}
    for slug, qty in merged.items():
        p = found[slug]
        lines.append({"product_id": str(p["id"]), "box_id": None, "name": p["name"],
                      "unit_price_cents": p["price_cents"], "qty": qty})
        total += p["price_cents"] * qty
        needs[str(p["id"])] = qty
    if total < MIN_PRODUCTS_TOTAL_CENTS:
        raise ValidationError({"total": MSG_MIN_TOTAL})
    return {"lines": lines, "total_cents": total, "stock_needs": needs}
