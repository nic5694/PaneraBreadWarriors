import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app
from app.database import db
from seed import seed_database


def reset_database(seed_data=True):
    app = create_app(seed_data=False)

    with app.app_context():
        with db.connection_context():
            db.execute_sql(
                "TRUNCATE TABLE events, urls, users RESTART IDENTITY CASCADE;"
            )

            if seed_data:
                seed_database()


def main():
    parser = argparse.ArgumentParser(
        description="Reset and optionally reseed the database for load tests."
    )
    parser.add_argument(
        "--no-seed",
        action="store_true",
        help="Truncate tables without reseeding them.",
    )
    args = parser.parse_args()

    reset_database(seed_data=not args.no_seed)


if __name__ == "__main__":
    main()