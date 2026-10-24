"""`flask seed`: datos iniciales idempotentes (se puede ejecutar varias veces)."""
from app.db.seed import catalog, pickups
from app.db.session import transaction


def run() -> None:
    with transaction() as conn:
        catalog.seed(conn)
        pickups.seed(conn)

      
