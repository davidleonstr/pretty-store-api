module.exports = {
  apps: [
    {
      name: 'prettystore-api',
      cwd: '/var/www/pretty-store-api',
      script: '.venv/bin/gunicorn',
      args: '--bind 127.0.0.1:5000 --workers 1 --threads 8 --timeout 60 --access-logfile - wsgi:app',
      interpreter: 'none',          // gunicorn es un ejecutable Python, no un script de Node
      autorestart: true,
      max_restarts: 10,
      restart_delay: 3000,
      max_memory_restart: '400M',
      env: { PYTHONUNBUFFERED: '1' },
    },
  ],
};