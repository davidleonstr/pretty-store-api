from werkzeug.middleware.proxy_fix import ProxyFix

from app import create_app

app = create_app()
# Confía en UN proxy (nginx) para IP y esquema
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)