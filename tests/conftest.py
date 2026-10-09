"""BD de prueba, cliente HTTP, admin y token de ejemplo.

Requiere una base PostgreSQL vacía y desechable en TEST_DATABASE_URL, p. ej.
  postgresql+psycopg://postgres:postgres@localhost:5432/prettystore_test
"""
import os
import pathlib

import pytest
from sqlalchemy import create_engine, text

SCHEMA = pathlib.Path(__file__).resolve().parents[1] / "schema.sql"
TEST_URL = os.environ.get("TEST_DATABASE_URL")

@pytest.fixture(scope="session")
def app():
    if not TEST_URL:
        pytest.skip("Define TEST_DATABASE_URL para correr las pruebas con BD")
    engine = create_engine(TEST_URL, isolation_level="AUTOCOMMIT")
    with engine.connect() as c:
        c.execute(text("DROP SCHEMA public CASCADE"))
        c.execute(text("CREATE SCHEMA public"))
        c.exec_driver_sql(SCHEMA.read_text(encoding="utf-8"))
    engine.dispose()

    from app import create_app

    return create_app({
        "DATABASE_URL": TEST_URL, "TESTING": True, "RATELIMIT_ENABLED": False,
        "JWT_SECRET_KEY": "test-secret-with-enough-length-0123456789",
        "UPLOAD_DIR": str(pathlib.Path(__file__).parent / "_uploads"),
    })

@pytest.fixture()
def client(app):
    return app.test_client()

@pytest.fixture(scope="session")
def admin_token(app):
    from app.core.db import transaction
    from app.modules.administradores import service

    with app.app_context(), transaction() as conn:
        service.create_admin(conn, "Admin Test", "admin@test.com", "una-clave-larga-123")
    c = app.test_client()
    res = c.post("/api/admin/login", json={"correo": "admin@test.com", "password": "una-clave-larga-123"})
    assert res.status_code == 200, res.get_json()
    return res.get_json()["accessToken"]

@pytest.fixture()
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}
