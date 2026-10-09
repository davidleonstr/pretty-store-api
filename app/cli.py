"""Comandos de Flask: flask create-admin, flask seed."""
import click

from app.core.db import transaction
from app.core.errors import AppError

def register_cli(app):
    @app.cli.command("create-admin")
    @click.option("--nombre", required=True, help="Nombre del administrador")
    @click.option("--correo", required=True, help="Correo del administrador")
    @click.password_option(help="Contraseña (mínimo 10 caracteres)")
    def create_admin(nombre, correo, password):
        from app.modules.administradores import schemas, service

        try:
            data = schemas.parse_create({"nombre": nombre, "correo": correo, "password": password})
            with transaction() as conn:
                row = service.create_admin(conn, data["nombre"], data["correo"], data["password"])
        except AppError as err:
            raise click.ClickException(f"{err.message} {getattr(err, 'fields', '') or ''}".strip())
        click.echo(f"Administrador creado: {row['correo']}")

    @app.cli.command("seed")
    def seed():
        from app.seed import run

        run()
        click.echo("Datos iniciales cargados.")
