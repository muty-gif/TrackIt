release: flask db upgrade
web: gunicorn --bind 0.0.0.0:$PORT --workers 3 --timeout 60 --access-logfile - wsgi:app
