from notion_calendar_sync.apps.flask.app import create_app

app = create_app()

# In a production environment, you would typically have another
# environment variable to load a production-specific config.
# For example:
#
# import os
# from calendar.apps.flask.config import ProdConfig
#
# if os.environ.get('FLASK_ENV') == 'production':
#     app = create_app(ProdConfig)
# else:
#     app = create_app()

application = app
