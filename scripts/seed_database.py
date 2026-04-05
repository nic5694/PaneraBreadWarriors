import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from app import create_app
from seed import seed_database


def main():
    app = create_app(seed_data=False)

    with app.app_context():
        seed_database()


if __name__ == "__main__":
    main()