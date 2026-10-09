"""`flask seed`: datos iniciales idempotentes (se puede ejecutar varias veces)."""
from app.core.db import transaction
from app.seed import catalog, pickups


def run() -> None:
    with transaction() as conn:
        catalog.seed(conn)
        pickups.seed(conn)
