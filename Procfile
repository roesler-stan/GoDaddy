web: gunicorn -k flask_sockets.worker app:app
worker: celery worker --app=tasks.app