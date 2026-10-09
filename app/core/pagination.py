from flask import request

def get_page_params(default_size: int = 20, max_size: int = 100) -> tuple[int, int, int, int]:
    """Devuelve (page, page_size, limit, offset)."""
    def _int(name, default):
        try:
            return int(request.args.get(name, default))
        except (TypeError, ValueError):
            return default

    page = max(1, _int("page", 1))
    size = min(max_size, max(1, _int("pageSize", default_size)))
    return page, size, size, (page - 1) * size
