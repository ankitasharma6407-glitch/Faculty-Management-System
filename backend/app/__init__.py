import os

from flask import Flask, jsonify, send_from_directory
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import HTTPException

from config import Config

from .extensions import cors, db, jwt, migrate
from .utils import ApiError, fail


def create_app(config_class=Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    cors.init_app(
        app,
        resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}},
        supports_credentials=True,
    )

    from .import models
    from .routes import register_blueprints
    from .routes.attendance import bp as attendance_bp
    from .routes.audit_logs import bp as audit_logs_bp
    from .routes.leave_requests import bp as leave_requests_bp

    app.register_blueprint(leave_requests_bp)
    app.register_blueprint(audit_logs_bp)
    app.register_blueprint(attendance_bp)

    register_blueprints(app)

    @app.get("/api/health")
    def health():
        return jsonify({
            "success": True,
            "status": "ok",
            "service": "FMPS API"
        })

    @app.get("/uploads/<path:filename>")
    def uploaded_file(filename):
        return send_from_directory(
            app.config["UPLOAD_FOLDER"],
            filename
        )

    # JWT error handlers
    @jwt.unauthorized_loader
    def _missing_token(reason):
        return fail("Authorization token is missing", 401)

    @jwt.invalid_token_loader
    def _invalid_token(reason):
        return fail("Invalid authorization token", 401)

    @jwt.expired_token_loader
    def _expired_token(header, payload):
        return fail("Session expired, please log in again", 401)

    # Error handlers
    @app.errorhandler(ApiError)
    def _api_error(err: ApiError):
        return fail(err.message, err.status, err.details)

    @app.errorhandler(IntegrityError)
    def _integrity_error(err: IntegrityError):
        db.session.rollback()
        return fail(
            "A record with these unique values already exists",
            409
        )

    @app.errorhandler(HTTPException)
    def _http_error(err: HTTPException):
        return fail(
            err.description or err.name,
            err.code or 500
        )

    @app.errorhandler(Exception)
    def _unhandled(err: Exception):
        db.session.rollback()
        app.logger.exception(err)
        return fail("Internal server error", 500)

    return app