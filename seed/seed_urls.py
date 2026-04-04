from app import create_app
from seed import seed_urls


app = create_app(seed_data=False)

with app.app_context():
    seed_urls()