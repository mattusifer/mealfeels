import os
import logging

from flask import Flask, render_template

from . import auth, db, tracking, home

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="[%(asctime)s %(levelname)s %(name)s] %(message)s",
)

logger = logging.getLogger(__name__)


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev",  # TODO: set this
        TEXTBELT_API_KEY=os.environ["TEXTBELT_API_KEY"],
        REPLY_WEBHOOK_URL=os.environ["REPLY_WEBHOOK_URL"],
    )

    app.config.from_pyfile("config.py", silent=True)

    # crate the instance dir
    os.makedirs(app.instance_path, exist_ok=True)

    @app.route("/health")
    def healthcheck():
        return "OK"

    @app.route("/")
    def index():
        return render_template("index.html")

    db.init_app(app)

    app.register_blueprint(auth.bp)
    app.register_blueprint(tracking.bp)
    app.register_blueprint(home.bp)

    return app
