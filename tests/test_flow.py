"""Flujo de extremo a extremo contra PostgreSQL real (requiere TEST_DATABASE_URL)."""
import pytest


@pytest.fixture(scope="module", autouse=True)
def seeded(app):
    from app.seed import run

    with app.app_context():
        run()


def _slot(client):
    pickups = client.get("/api/pickups").get_json()
    assert pickups, "el seed debe dejar puntos con horas futuras"
    p = pickups[0]
    return p["id"], p["hours"][0]["id"]


def _order_body(client, **over):
    pid, hid = _slot(client)
    body = {
        "kind": "productos",
        "items": [{"slug": "vela-de-vainilla", "qty": 1}],
        "customer": {"nombres": "Ana", "apellidos": "López", "celular": "7777-8888", "correo": "ana@test.com"},
        "pickupId": pid, "horaId": hid, "nota": "",
    }
    body.update(over)
    return body


def test_health_and_catalog(client):
    assert client.get("/api/health").get_json() == {"status": "ok"}
    prods = client.get("/api/products").get_json()
    assert len(prods) >= 6 and prods[0]["photos"][0].get("emoji")
    detail = client.get("/api/products/mascarilla-de-fresa").get_json()
    assert detail["inBoxes"]
    boxes = client.get("/api/boxes").get_json()
    assert boxes and client.get("/api/boxes/tags").get_json()
    assert client.get(f"/api/boxes/{boxes[0]['slug']}").get_json()["contents"]
    assert client.get(f"/api/boxes/{boxes[0]['slug']}/availability").get_json()["available"] is True


def test_order_lifecycle_and_stock(client, admin_headers):
    stock = lambda: next(p for p in client.get("/api/admin/products", headers=admin_headers).get_json()
                         if p["slug"] == "vela-de-vainilla")["stock"]
    before = stock()
    res = client.post("/api/orders", json=_order_body(client))
    assert res.status_code == 201, res.get_json()
    order = res.get_json()
    assert order["code"].startswith("PS-") and order["totalCents"] == 350
    assert stock() == before - 1

    got = client.get(f"/api/orders/{order['id']}").get_json()
    assert got["canModify"] is True and got["customer"]["correo"] == "ana@test.com"

    res = client.patch(f"/api/orders/{order['id']}", json={"nota": "Gracias"})
    assert res.status_code == 200 and res.get_json()["nota"] == "Gracias"

    res = client.post(f"/api/orders/{order['id']}/cancel")
    assert res.status_code == 200 and res.get_json()["status"] == "cancelado"
    assert stock() == before
    assert client.post(f"/api/orders/{order['id']}/cancel").status_code == 200
    assert stock() == before  # idempotente

    by_code = client.get(f"/api/admin/orders/by-code/{order['code']}", headers=admin_headers)
    assert by_code.status_code == 200


def test_validation_and_rules(client):
    assert client.post("/api/orders", json={}).status_code == 422
    # mínimo de $3.00 en productos sueltos
    res = client.post("/api/orders", json=_order_body(client, items=[{"slug": "balsamo-de-labios", "qty": 1}]))
    assert res.status_code == 422 and "total" in res.get_json()["error"]["fields"]
    assert client.get("/api/orders/no-es-uuid").status_code == 404


def test_box_order_and_admin_status(client, admin_headers):
    slug = client.get("/api/boxes").get_json()[0]["slug"]
    res = client.post("/api/orders", json=_order_body(client, kind="caja", items=[{"slug": slug, "qty": 1}]))
    assert res.status_code == 201, res.get_json()
    oid = res.get_json()["id"]
    res = client.patch(f"/api/admin/orders/{oid}/status", json={"status": "entregado"}, headers=admin_headers)
    assert res.status_code == 200 and res.get_json()["deliveredAt"]
    assert client.post(f"/api/orders/{oid}/cancel").status_code == 409
    listing = client.get("/api/admin/orders?status=entregado&pageSize=5", headers=admin_headers).get_json()
    assert listing["total"] >= 1


def test_auth_required(client):
    assert client.get("/api/admin/products").status_code == 401
    assert client.get("/api/admin/me", headers={"Authorization": "Bearer x"}).status_code == 401
    bad = client.post("/api/admin/login", json={"correo": "nadie@test.com", "password": "x"})
    assert bad.status_code == 401


def test_admin_crud(client, admin_headers):
    cat = client.post("/api/admin/categorias", json={"nombre": "Nueva"}, headers=admin_headers)
    assert cat.status_code == 201
    dup = client.post("/api/admin/categorias", json={"nombre": "nueva"}, headers=admin_headers)
    assert dup.status_code == 409
    prod = client.post("/api/admin/products", headers=admin_headers, json={
        "name": "Producto Prueba", "priceCents": 500, "categoriaId": cat.get_json()["id"], "stock": 3})
    assert prod.status_code == 201, prod.get_json()
    pid = prod.get_json()["id"]
    assert client.patch(f"/api/admin/products/{pid}/stock", json={"delta": -3}, headers=admin_headers).get_json()["soldOut"]
    assert client.patch(f"/api/admin/products/{pid}/stock", json={"delta": -1}, headers=admin_headers).status_code == 409
    assert client.delete(f"/api/admin/products/{pid}", headers=admin_headers).status_code == 204
    hora = client.post("/api/admin/horas", json={"hora": "11:15"}, headers=admin_headers)
    assert hora.status_code == 201
    assert client.delete(f"/api/admin/horas/{hora.get_json()['id']}", headers=admin_headers).status_code == 204
    assert client.get("/api/admin/pickups", headers=admin_headers).status_code == 200


def test_media_upload(client, admin_headers):
    import io

    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (40, 30), "pink").save(buf, "PNG")
    res = client.post("/api/admin/images", headers=admin_headers,
                      data={"file": (io.BytesIO(buf.getvalue()), "x.png"), "alt": "rosa"},
                      content_type="multipart/form-data")
    assert res.status_code == 201, res.get_json()
    img = res.get_json()
    assert client.get(img["src"]).status_code == 200
    fake = client.post("/api/admin/images", headers=admin_headers,
                       data={"file": (io.BytesIO(b"no soy imagen"), "x.png")}, content_type="multipart/form-data")
    assert fake.status_code == 415
    assert client.delete(f"/api/admin/images/{img['id']}", headers=admin_headers).status_code == 204


def test_manage_order_by_code(client):
    o = client.post("/api/orders", json=_order_body(client)).get_json()
    for key in (o["code"], o["code"].lower()):  # el código funciona como llave, sin importar mayúsculas
        assert client.get(f"/api/orders/{key}").get_json()["id"] == o["id"]
    assert client.patch(f"/api/orders/{o['code']}", json={"nota": "Por código"}).get_json()["nota"] == "Por código"
    assert client.post(f"/api/orders/{o['code']}/cancel").get_json()["status"] == "cancelado"
    assert client.get("/api/orders/PS-ZZZZZZ").status_code == 404
    assert client.get("/api/orders/ps-123").status_code == 404
