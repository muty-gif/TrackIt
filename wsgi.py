"""Production WSGI entry point.

Development uses ``app.py``; production servers should import this module.

    gunicorn --bind 0.0.0.0:$PORT --workers 3 wsgi:app
"""

from trackit import create_app

app = create_app()
