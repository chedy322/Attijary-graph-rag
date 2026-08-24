import os
from flask import Flask, jsonify
from config.database import db
from config.celery_app import celery_client
from core.exceptions import register_error_handlers
from core.middleware import require_auth, admin_required
import logging
from dotenv import load_dotenv
from config.database import migrate
from config.vector_db import weaviate_client
from config.llm import llm_singleton
from flask_cors import CORS

load_dotenv()


def create_app() -> Flask:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    app = Flask(__name__)
    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": ["http://localhost:3000", "https://yourfrontend.com"]
            }
        },
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization", "Access-Control-Allow-Headers"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    )
    import urllib.parse  # 1. Add this import at the top of your file

    # Configure app from environment variables
    USER = os.getenv("user")
    PASSWORD = os.getenv("password")
    HOST = os.getenv("host")
    DBPORT = os.getenv("dbport")
    DBNAME = os.getenv("dbname")

    # 2. URL encode the password safely to handle special characters like '@'
    ENCODED_PASSWORD = urllib.parse.quote_plus(PASSWORD) if PASSWORD else ""

    # 3. Use ENCODED_PASSWORD instead of PASSWORD in the F-string
    DATABASE_URL = f"postgresql+psycopg2://{USER}:{ENCODED_PASSWORD}@{HOST}:{DBPORT}/{DBNAME}?sslmode=require"
    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL or os.getenv(
        "postgresql://postgres:postgres@localhost:5432/regulatory_db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_size": 10,  # Keep 10 ready connections open at all times
        "max_overflow": 5,  # Allow 5 extra connections if traffic spikes
        "pool_timeout": 30,  # Wait 30 seconds for a free connection before failing
        "pool_recycle": 1800,  # Refresh connections every 30 mins to prevent drops
        "pool_pre_ping": True,  # Check if a ready connection is alive before using it
    }
    # Initialize SQLAlchemy Singleton with App
    db.init_app(app)
    migrate.init_app(app, db)

    # Register core global error handlers
    register_error_handlers(app)

    # Connect to Weaviate client (singleton)
    # weaviate_client.get_client()
    # # Initialize the llm
    # llm_singleton.get_llm()
    # llm_singleton.get_embedding_model()

    # CELERY CONFIGURATION
    app.config["CELERY"] = dict(
        broker_url=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
        result_backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
        imports=[
            "tasks.indexing_tasks",
            "tasks.deletion_tasks",
        ],  # Force tasks to register
    )
    celery_app = celery_client.init_app(app)
    print("Celery client initialized successfully.")

    # Register Blueprints
    from api.document_routes import document_bp
    from api.auth_routes import auth_bp
    from api.agent_routes import agent_bp

    app.register_blueprint(agent_bp, url_prefix="/api/v1/agent")
    app.register_blueprint(document_bp, url_prefix="/api/v1/documents")
    app.register_blueprint(auth_bp, url_prefix="/api/v1/sync")

    @app.route("/health", methods=["GET"])
    def health_check():
        from tasks.indexing_tasks import run_indexing_pipeline

        return jsonify(
            {"status": "healthy", "environment": os.getenv("FLASK_ENV", "development")}
        ), 200

    @app.route("/api/v1/protected-route-test", methods=["GET"])
    @require_auth
    def protected_test():
        from flask import g

        return jsonify(
            {"message": "Access granted to authenticated user", "user_id": g.user_id}
        ), 200

    @app.route("/api/v1/admin-route-test", methods=["GET"])
    @require_auth
    @admin_required
    def admin_test():
        from flask import g

        return jsonify(
            {"message": "Access granted to admin", "user_id": g.user_id}
        ), 200

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
