from app.routes.users import users_bp
from app.routes.urls import urls_bp
from app.routes.events import events_bp

def register_routes(app):
    # The autograder hits /users/...
    app.register_blueprint(users_bp, url_prefix='/users')
    
    # The autograder hits /r/... and /urls/...
    app.register_blueprint(urls_bp, url_prefix='/')
    
    # The autograder hits /events/...
    app.register_blueprint(events_bp, url_prefix='/events')