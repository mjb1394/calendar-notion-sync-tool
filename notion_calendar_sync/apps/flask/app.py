import atexit
from flask import Flask

from notion_calendar_sync.apps.flask.config import Config
from notion_calendar_sync.apps.flask.routes.main import main_bp
from notion_calendar_sync.logging_config import setup_logging
from notion_calendar_sync.web.scheduler import scheduler


def create_app(config_class=Config):
    setup_logging()
    """
    Creates and configures the Flask application.
    """
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(config_class)

    # Register blueprints
    app.register_blueprint(main_bp)

    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())

    return app


app = create_app()

if __name__ == "__main__":
    # For development only
    app.run(host=app.config["HOST"], port=app.config["PORT"], debug=app.config["DEBUG"])
