from app.routes.users import users_bp
from app.routes.urls import urls_bp
from app.routes.events import events_bp


def register_routes(app):
    # Users API
    app.register_blueprint(users_bp, url_prefix='/users/v1/api/users')

    # URLs blueprint defines both /urls/v1/api/urls/* and /r/<shortcode> paths.
    app.register_blueprint(urls_bp)

    # events_bp already includes /events/v1/api/events as its blueprint prefix.
    app.register_blueprint(events_bp)