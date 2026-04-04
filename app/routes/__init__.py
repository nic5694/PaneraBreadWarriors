from app.routes.users import users_bp
from app.routes.urls import urls_bp
from app.routes.events import events_bp

def register_routes(app):
    # This aligns your @users_bp routes with the /users endpoints
    app.register_blueprint(users_bp, url_prefix='/users')
    
    # Keeps /r/ and /urls/ accessible at the root
    app.register_blueprint(urls_bp, url_prefix='/')
    
    # Matches /events endpoints
    app.register_blueprint(events_bp, url_prefix='/events')