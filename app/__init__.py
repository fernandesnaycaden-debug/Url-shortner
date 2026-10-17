from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.exceptions import HTTPException

from .config import Config

# Created here (without an app) so models.py can import it; bound in create_app().
db = SQLAlchemy()


def create_app(config_overrides=None):
    """Application factory: builds a fresh app, so tests can use their own config."""
    app = Flask(__name__)
    app.config.from_object(Config)
    if config_overrides:
        app.config.update(config_overrides)

    db.init_app(app)

    from .routes import bp
    app.register_blueprint(bp)

    # Turn every HTTP error (404, 405, 410, ...) into JSON instead of Flask's HTML page.
    @app.errorhandler(HTTPException)
    def handle_http_error(err):
        return jsonify(error=err.description), err.code

    with app.app_context():
        from . import models  # noqa: F401  (registers the table with SQLAlchemy)
        db.create_all()

    return app
