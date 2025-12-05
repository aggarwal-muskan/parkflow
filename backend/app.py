from flask import Flask
from flask_cors import CORS

from backend.config import Config
from backend.models import init_db
from backend.routes.auth import auth_bp
from backend.routes.admin import admin_bp
from backend.routes.user import user_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app, supports_credentials=True)

    with app.app_context():
        init_db()

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(user_bp, url_prefix="/api/user")

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
