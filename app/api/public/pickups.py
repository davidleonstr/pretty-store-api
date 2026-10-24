from flask import Blueprint

from app.core.http import ok
from app.schemas import pickups as schemas
from app.services import pickups as service

bp = Blueprint("pickups_public", __name__, url_prefix="/api/pickups")

@bp.get("")
def list_pickups():
    return ok([schemas.to_public(p) for p in service.list_public()])

        
