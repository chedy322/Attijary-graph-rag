# config/celery_app.py
from celery import Celery, Task
from flask import Flask


class CeleryClient:
    def __init__(self):
        self._app = None

    def init_app(self, app: Flask) -> Celery:
        """Initializes Celery with the Flask application context."""

        class FlaskTask(Task):
            def __call__(self, *args: object, **kwargs: object) -> object:
                with app.app_context():
                    return self.run(*args, **kwargs)

        # Initialize the Celery app instance
        celery_app = Celery(app.name, task_cls=FlaskTask)

        # Pull Celery configs directly from Flask app config settings
        celery_app.config_from_object(app.config.get("CELERY", {}))
        celery_app.set_default()

        self._app = celery_app
        return celery_app

    def get_app(self) -> Celery:
        if not self._app:
            # Fallback to an empty instance so the worker can load modules safely at boot
            self._app = Celery("default_app")
        return self._app


celery_client = CeleryClient()
