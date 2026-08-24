from app import create_app
from config.celery_app import celery_client

# 1. Initialize the Flask application to trigger create_app()
flask_app = create_app()

# 2. Extract the fully configured Celery instance
celery_app = celery_client.get_app()
