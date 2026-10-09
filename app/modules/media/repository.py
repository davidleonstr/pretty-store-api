from app.core.db import execute, fetch_all, fetch_one

_COLS = "id, storage_key, original_name, mime_type, size_bytes, width, height, alt_text, created_at"

def insert(conn, storage_key, original_name, mime_type, size_bytes, width, height, alt_text, uploaded_by) -> dict:
    return fetch_one(
        conn,
        f"""INSERT INTO images (storage_key, original_name, mime_type, size_bytes, width, height, alt_text, uploaded_by)
            VALUES (:k, :o, :m, :s, :w, :h, :a, :u) RETURNING {_COLS}""",
        {"k": storage_key, "o": original_name, "m": mime_type, "s": size_bytes,
         "w": width, "h": height, "a": alt_text, "u": uploaded_by},
    )

def get_by_id(conn, image_id: str) -> dict | None:
    return fetch_one(conn, f"SELECT {_COLS} FROM images WHERE id = :id", {"id": image_id})

def count_existing(conn, image_ids: list[str]) -> int:
    if not image_ids:
        return 0
    row = fetch_one(conn, "SELECT count(*) AS n FROM images WHERE id = ANY(CAST(:ids AS uuid[]))", {"ids": image_ids})
    return row["n"]

def list_page(conn, limit: int, offset: int) -> list[dict]:
    return fetch_all(
        conn,
        f"""SELECT {_COLS},
                   (SELECT count(*) FROM product_images pi WHERE pi.image_id = images.id) AS used_products,
                   (SELECT count(*) FROM box_images bi WHERE bi.image_id = images.id) AS used_boxes
            FROM images ORDER BY created_at DESC LIMIT :l OFFSET :o""",
        {"l": limit, "o": offset},
    )

def count_all(conn) -> int:
    return fetch_one(conn, "SELECT count(*) AS n FROM images")["n"]

def is_used(conn, image_id: str) -> bool:
    row = fetch_one(
        conn,
        """SELECT (EXISTS (SELECT 1 FROM product_images WHERE image_id = :id)
                OR EXISTS (SELECT 1 FROM box_images WHERE image_id = :id)) AS used""",
        {"id": image_id},
    )
    return row["used"]

def update_alt(conn, image_id: str, alt_text: str) -> dict | None:
    return fetch_one(
        conn, f"UPDATE images SET alt_text = :a WHERE id = :id RETURNING {_COLS}", {"id": image_id, "a": alt_text}
    )

def delete(conn, image_id: str) -> int:
    return execute(conn, "DELETE FROM images WHERE id = :id", {"id": image_id})
