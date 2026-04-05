from app.routes.users import users_bp
from app.routes.urls import urls_bp
from app.routes.events import events_bp
from app.routes.redirect import redirect_bp


def register_routes(app):
    app.register_blueprint(users_bp, url_prefix='/users')
    app.register_blueprint(urls_bp, url_prefix='/urls')
    app.register_blueprint(events_bp, url_prefix='/events')
    app.register_blueprint(redirect_bp, url_prefix='/r')