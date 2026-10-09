"""Almacenamiento en disco (UPLOAD_DIR)."""
import os

from flask import current_app

def upload_dir() -> str:
    path = os.path.abspath(current_app.config["UPLOAD_DIR"])
    os.makedirs(path, exist_ok=True)
    return path

def _path(storage_key: str) -> str:
    base = upload_dir()
    full = os.path.abspath(os.path.join(base, storage_key))
    if os.path.dirname(full) != base:  # anti path traversal
        raise ValueError("storage_key inválida")
    return full

def save(storage_key: str, data: bytes) -> None:
    with open(_path(storage_key), "wb") as fh:
        fh.write(data)

def delete(storage_key: str) -> None:
    try:
        os.remove(_path(storage_key))
    except (FileNotFoundError, ValueError):
        pass
