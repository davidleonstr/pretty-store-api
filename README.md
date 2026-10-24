# Pretty Store - API

API REST de **Pretty Store**, una tienda de reservas con retiro en persona (sin envíos ni pago en línea).
Construida con **Flask + PostgreSQL**, SQL explícito con SQLAlchemy Core (sin ORM).

- Zona horaria del negocio: `America/El_Salvador` (UTC-6). Precios en **centavos de USD** (enteros).

## Requisitos

| Herramienta | Versión |
|---|---|
| Python | 3.11 o superior |
| PostgreSQL | 14 o superior (usa las extensiones `pgcrypto` y `citext`) |

## Puesta en marcha (desarrollo)

```bash
cd pretty-store-api
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Base de datos
createdb prettystore
psql -d prettystore -f schema.sql          # aplícalo UNA vez en una base vacía

cp .env.example .env                        # edita los valores
flask --app wsgi create-admin --nombre "Tu Nombre" --correo tu@correo.com
flask --app wsgi seed                       # opcional: datos de ejemplo
flask --app wsgi run -p 5000 --debug
```

Comprueba que funciona: `curl http://localhost:5000/api/health` → `{"status":"ok"}`.

## Variables de entorno

Se leen del entorno o de un archivo `.env` en `backend/`.

| Variable | Por defecto | Descripción |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg://postgres:postgres@localhost:5432/prettystore` | Conexión a PostgreSQL |
| `JWT_SECRET_KEY` | `dev-secret-change-me` | **Cámbiala en producción.** Larga y aleatoria (`openssl rand -hex 48`) |
| `JWT_ACCESS_MINUTES` | `60` | Vida del token de acceso |
| `JWT_REFRESH_DAYS` | `7` | Vida del token de renovación |
| `UPLOAD_DIR` | `./uploads` | Carpeta donde se guardan las imágenes subidas |
| `MEDIA_BASE_URL` | `/media` | Prefijo público de las imágenes |
| `MAX_UPLOAD_MB` | `5` | Tamaño máximo por imagen |
| `CORS_ORIGINS` | `http://localhost:5173` | Orígenes permitidos, separados por coma |
| `RATELIMIT_ENABLED` | `1` | `0` desactiva los límites de peticiones |
| `RATELIMIT_STORAGE_URI` | `memory://` | Almacén de los límites (ej. `redis://localhost:6379`) |

## Estructura

```
pretty-store-api/
├─ wsgi.py              # punto de entrada (app = create_app())
├─ schema.sql           # esquema PostgreSQL: fuente de verdad de la BD
├─ app/
│  ├─ __init__.py       # fábrica de la app, registro de módulos
│  ├─ config.py         # configuración desde variables de entorno
│  ├─ cli.py            # comandos: create-admin, seed
│  ├─ core/             # BD, errores, validación, paginación (no importa módulos)
│  ├─ extensions.py     # JWT, CORS, rate limiter
│  └─ modules/          # un paquete por dominio (ver abajo)
└─ tests/
```

Cada módulo en `app/modules/<nombre>/` separa sus capas: `routes_*` → `schemas` (validación) → `service` (reglas de negocio) → `repository` (SQL).
Las rutas nunca importan el repositorio y los módulos solo se importan entre sí por paquete; `tests/test_architecture.py` lo verifica.

Módulos: `administradores`, `auth`, `media`, `categorias`, `products`, `boxes`, `horas`, `pickups`, `clientes`, `orders`.

## Convenciones de la API

- **JSON** en peticiones y respuestas, UTF-8.
- **Errores** con un formato único:
  ```json
  { "error": { "code": "validation_error", "message": "Datos inválidos", "fields": { "correo": "Escribe un correo válido" } } }
  ```
  | HTTP | Cuándo |
  |---|---|
  | 401 | Sin sesión, token inválido o vencido |
  | 404 | No existe el recurso |
  | 409 | Conflicto de reglas: `out_of_stock`, `order_locked`, `in_use`, `has_orders`, `slug_taken`, `email_taken`… |
  | 413 / 415 | Imagen demasiado grande / formato no permitido |
  | 422 | Validación; `fields` indica el error por campo |
  | 429 | Límite de peticiones excedido |
- **Paginación** en listados de administración: `?page=1&pageSize=20` → `{ items, total, page, pageSize }`.
- **Autenticación admin**: `Authorization: Bearer <accessToken>`. El token de renovación se canjea en `/api/admin/refresh`.

## Endpoints

### Públicos (tienda)

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/health` | Estado del servicio |
| GET | `/api/products` · `/api/products/<slug>` | Catálogo y detalle de productos |
| GET | `/api/products/<slug>/availability` | Disponibilidad de un producto |
| GET | `/api/boxes` · `/api/boxes/tags` · `/api/boxes/<slug>` | Cajitas, etiquetas y detalle |
| GET | `/api/boxes/<slug>/availability` | Disponibilidad de una cajita |
| GET | `/api/pickups` | Puntos de retiro con sus fechas y horas futuras |
| POST | `/api/orders` | Crear una reserva (devuelve `id`, `code`, `status`, `totalCents`) |
| GET · PATCH | `/api/orders/<llave>` | Ver / modificar una reserva |
| POST | `/api/orders/<llave>/cancel` | Cancelar una reserva (idempotente) |
| GET | `/media/<storage_key>` | Imágenes subidas |

`<llave>` es el **código** que recibe el cliente (`PS-ABC123`, sin distinguir mayúsculas) o el `id` (uuid) del pedido.
Solo se puede modificar o cancelar mientras el estado sea `pendiente`; si no, responde `409 order_locked`.

### Administración (requieren token, salvo login y refresh)

| Recurso | Rutas bajo `/api/admin` |
|---|---|
| Sesión | `POST /login` · `POST /refresh` · `GET /me` · `POST /me/password` |
| Administradores | `GET, POST /administradores` · `PATCH, DELETE /administradores/<id>` |
| Pedidos | `GET /orders` · `GET /orders/<id>` · `GET /orders/by-code/<code>` · `PATCH /orders/<id>/status` |
| Productos | `GET, POST /products` · `GET, PATCH, DELETE /products/<id>` · `PATCH /products/<id>/stock` |
| Cajitas | `GET, POST /boxes` · `GET, PATCH, DELETE /boxes/<id>` · `GET /caja-tipos` |
| Categorías | `GET, POST /categorias` · `PATCH, DELETE /categorias/<id>` |
| Puntos de retiro | `GET, POST /pickups` · `PATCH, DELETE /pickups/<id>` · `GET /pickups/sin-horarios` |
| Fechas y horas de retiro | `POST /pickups/<id>/fechas` · `PATCH, DELETE …/fechas/<fecha_id>` · `POST …/fechas/<fecha_id>/horas` · `PATCH, DELETE …/horas/<slot_id>` |
| Catálogo de horas | `GET, POST /horas` · `DELETE /horas/<id>` |
| Imágenes | `GET, POST /images` (multipart, campo `file`) · `PATCH, DELETE /images/<id>` |

### Crear una reserva

```http
POST /api/orders
Content-Type: application/json

{
  "kind": "productos",                       // "productos" | "caja"
  "items": [{ "slug": "vela-de-vainilla", "qty": 1 }],
  "customer": { "nombres": "Ana", "apellidos": "López", "celular": "7777-8888", "correo": "ana@correo.com" },
  "pickupId": "…", "horaId": "…",            // de GET /api/pickups
  "nota": ""
}
```

Reglas: mínimo de **$3.00** en productos sueltos; el stock se descuenta al reservar y se repone al cancelar.
Estados: `pendiente` → `en proceso` → `por entregar` → `entregado` (o `cancelado`).

## Límites de peticiones

| Ruta | Límite |
|---|---|
| `POST /api/admin/login` | 5 por minuto |
| `POST /api/orders` | 10 por hora por IP |
| `GET/PATCH /api/orders/<llave>` y `POST …/cancel` | 30 por hora por IP (compartido) |

Detrás de un proxy (nginx) la IP real se toma de `X-Forwarded-For`; ver `DEPLOY.md` (ProxyFix). Con varios workers y `memory://` cada worker cuenta por separado: usa Redis en `RATELIMIT_STORAGE_URI`.

## Seguridad

- Contraseñas con **argon2**; JWT con rol `admin`; imágenes revalidadas y reprocesadas con Pillow.
- El **código de reserva** es la llave que protege los datos del cliente: no lo registres en logs ni lo expongas en analítica.
- En producción cambia `JWT_SECRET_KEY`, no uses `--debug` y limita `CORS_ORIGINS` a tu dominio.

## Pruebas

Requieren una base PostgreSQL **vacía y desechable** (la prueba borra el esquema `public`):

```bash
createdb prettystore_test
TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/prettystore_test python -m pytest tests -q
```

Sin `TEST_DATABASE_URL` las pruebas con base de datos se omiten.

## Comandos útiles

```bash
flask --app wsgi create-admin --nombre "…" --correo "…"   # crea un administrador
flask --app wsgi seed                                      # datos de ejemplo (solo desarrollo)
```
