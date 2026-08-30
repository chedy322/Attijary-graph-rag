import os
import urllib.parse
import logging
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

from config.database import db, migrate
from config.celery_app import celery_client
from core.exceptions import register_error_handlers
from core.middleware import require_auth, admin_required
import logging
load_dotenv()
logger = logging.getLogger(__name__)
 
def create_app() -> Flask:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    app = Flask(__name__)
    app.url_map.strict_slashes = False

    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:4200")
    logger.info(f"FRONTEND_URL is set to: {FRONTEND_URL}")

    ALLOWED_ORIGINS = [
        FRONTEND_URL,
        "http://localhost:4200",
        "http://127.0.0.1:4200",
        "http://localhost:3000",
    ]

    CORS(
        app,
        resources={r"/api/*": {"origins": ALLOWED_ORIGINS}},
        supports_credentials=True,
        allow_headers=[
            "Content-Type",
            "Authorization",
            "Access-Control-Allow-Headers",
            "X-Requested-With",
            "Accept",
        ],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        always_send=True,
    )

    # Database Configuration
    USER = os.getenv("user")
    PASSWORD = os.getenv("password")
    HOST = os.getenv("host")
    DBPORT = os.getenv("dbport")
    DBNAME = os.getenv("dbname")

    ENCODED_PASSWORD = urllib.parse.quote_plus(PASSWORD) if PASSWORD else ""

    if USER and HOST and DBNAME:
        DATABASE_URL = f"postgresql+psycopg2://{USER}:{ENCODED_PASSWORD}@{HOST}:{DBPORT}/{DBNAME}?sslmode=require"
    else:
        # Fallback URI if individual DB env vars aren't populated
        DATABASE_URL = os.getenv(
            "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/regulatory_db"
        )

    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_size": 10,
        "max_overflow": 5,
        "pool_timeout": 30,
        "pool_recycle": 1800,
        "pool_pre_ping": True,
    }

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    

    # Celery Setup
    app.config["CELERY"] = dict(
        broker_url=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
        result_backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
        imports=[
            "tasks.indexing_tasks",
            "tasks.deletion_tasks",
        ],
    )
    celery_app = celery_client.init_app(app)
    logger.info("Celery client initialized successfully.")

    # Register Blueprints
    from api.document_routes import document_bp
    from api.auth_routes import auth_bp
    from api.agent_routes import agent_bp
    from api.scraper_routes import scraper_bp

    app.register_blueprint(agent_bp, url_prefix="/api/v1/agent")
    app.register_blueprint(document_bp, url_prefix="/api/v1/documents")
    app.register_blueprint(auth_bp, url_prefix="/api/v1/sync")
    app.register_blueprint(scraper_bp, url_prefix="/api/v1/scraper")

    @app.route("/health", methods=["GET"])
    def health_check():
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

    # Catch internal server errors and guarantee CORS header propagation
    @app.errorhandler(Exception)
    def handle_exception(e):
        logger.error(f"Backend Exception Triggered: {e}")
        response = jsonify({"error": "Internal Server Error", "details": str(e)})
        response.status_code = getattr(e, "code", 500)

        origin = request.headers.get("Origin")
        if origin in ALLOWED_ORIGINS:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"

        return response
    @app.after_request
    def force_cors_headers(response):
        origin = request.headers.get("Origin")
        if origin in ALLOWED_ORIGINS:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With, Accept"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        return response
    register_error_handlers(app)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)