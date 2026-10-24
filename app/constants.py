"""Constantes de dominio compartidas. No depende de ninguna otra parte de la app."""

# ---- Autenticación -------------------------------------------------------------
MIN_PASSWORD = 10
MSG_PASSWORD = f"La contraseña debe tener al menos {MIN_PASSWORD} caracteres"

# ---- Zona horaria y etiquetas de fecha -----------------------------------------
TZ_NAME = "America/El_Salvador"
DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]

# ---- Catálogo ------------------------------------------------------------------
DEFAULT_EMOJI = "🎁"

# ---- Pedidos -------------------------------------------------------------------
ORDER_STATUSES = ("pendiente", "en proceso", "por entregar", "entregado", "cancelado")
ORDER_KINDS = ("caja", "productos")
MIN_PRODUCTS_TOTAL_CENTS = 300
MSG_MIN_TOTAL = "Los pedidos de productos sueltos deben sumar al menos $3.00"

# ---- Imágenes ------------------------------------------------------------------
IMAGE_MAX_SIDE = 2000
IMAGE_FORMATS = {  # formato de Pillow -> (mime, extensión)
    "JPEG": ("image/jpeg", "jpg"),
    "PNG": ("image/png", "png"),
    "WEBP": ("image/webp", "webp"),
    "GIF": ("image/gif", "gif"),
}
