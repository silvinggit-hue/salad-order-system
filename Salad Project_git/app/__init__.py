from flask import Flask
from config import Config
from app.models import db


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    db.init_app(app)

    with app.app_context():
        db.create_all()

    from app.routes import main
    app.register_blueprint(main)

    return app