"""Validación por contenido y normalización de imágenes con Pillow."""
import io
from dataclasses import dataclass

from PIL import Image, ImageOps, UnidentifiedImageError

from app.core.errors import UnsupportedMediaType

MAX_SIDE = 2000
_FORMATS = {
    "JPEG": ("image/jpeg", "jpg"),
    "PNG": ("image/png", "png"),
    "WEBP": ("image/webp", "webp"),
    "GIF": ("image/gif", "gif"),
}

@dataclass
class Processed:
    data: bytes
    mime_type: str
    ext: str
    width: int
    height: int

def process_image(raw: bytes) -> Processed:
    """Valida que sea JPEG/PNG/WebP/GIF real, quita EXIF y limita el lado mayor a 2000 px."""
    try:
        probe = Image.open(io.BytesIO(raw))
        probe.verify()  # detecta archivos corruptos; invalida el objeto
        img = Image.open(io.BytesIO(raw))
        fmt = (img.format or "").upper()
        if fmt not in _FORMATS:
            raise UnsupportedMediaType()
        mime, ext = _FORMATS[fmt]

        animated = fmt in ("GIF", "WEBP") and getattr(img, "n_frames", 1) > 1
        needs_resize = max(img.size) > MAX_SIDE

        if animated and not needs_resize:
            out = io.BytesIO()
            img.save(out, format=fmt, save_all=True, **({"loop": 0} if fmt == "GIF" else {"quality": 85}))
            data = out.getvalue()
            return Processed(data, mime, ext, img.width, img.height)

        img.seek(0)
        img = ImageOps.exif_transpose(img)  # respeta la orientación antes de quitar EXIF
        if needs_resize:
            img.thumbnail((MAX_SIDE, MAX_SIDE), Image.LANCZOS)

        out = io.BytesIO()
        if fmt == "JPEG":
            if img.mode not in ("RGB", "L"):
                img = img.convert("RGB")
            img.save(out, format="JPEG", quality=85, optimize=True)
        elif fmt == "PNG":
            img.save(out, format="PNG", optimize=True)
        elif fmt == "WEBP":
            img.save(out, format="WEBP", quality=85)
        else:  # GIF (un solo cuadro o reducido)
            img.save(out, format="GIF")
        return Processed(out.getvalue(), mime, ext, img.width, img.height)
    except UnsupportedMediaType:
        raise
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError, Image.DecompressionBombError, EOFError):
        raise UnsupportedMediaType("El archivo no es una imagen válida (JPEG, PNG, WebP o GIF)")
