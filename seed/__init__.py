import csv
import json
from datetime import datetime
from pathlib import Path

from app.database import db
from app.models.events import Event
from app.models.urls import Url
from app.models.users import User


SEED_DIR = Path(__file__).resolve().parent


def _parse_bool(value):
    return str(value).strip().lower() == "true"


def _parse_datetime(value):
    return datetime.fromisoformat(value) if value else None


def _sync_sequence(model):
    table_name = model._meta.table_name
    pk_column = model._meta.primary_key.column_name

    cursor = db.execute_sql(
        "SELECT pg_get_serial_sequence(%s, %s)",
        (table_name, pk_column),
    )
    sequence_name = cursor.fetchone()[0]

    if not sequence_name:
        return

    db.execute_sql(
        f'''
        SELECT setval(
            %s,
            COALESCE((SELECT MAX("{pk_column}") FROM "{table_name}"), 1),
            (SELECT MAX("{pk_column}") IS NOT NULL FROM "{table_name}")
        )
        ''',
        (sequence_name,),
    )


def seed_users():
    User.delete().execute()

    with (SEED_DIR / "users.csv").open(newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            User.create(
                id=int(row["id"]),
                name=row["username"],
                email=row["email"],
                password_hash=row["username"],
                created_at=_parse_datetime(row["created_at"]),
            )


def seed_urls():
    Url.delete().execute()

    with (SEED_DIR / "urls.csv").open(newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            Url.create(
                id=int(row["id"]),
                user_id=str(row["user_id"]) if row["user_id"] else None,
                shortcode=row["short_code"],
                original_url=row["original_url"],
                title=row["title"] or None,
                is_active=_parse_bool(row["is_active"]),
                created_at=_parse_datetime(row["created_at"]),
                updated_at=_parse_datetime(row["updated_at"]),
            )


def seed_events():
    Event.delete().execute()

    with (SEED_DIR / "events.csv").open(newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            Event.create(
                id=int(row["id"]),
                url_id=str(row["url_id"]),
                user_id=str(row["user_id"]) if row["user_id"] else None,
                event_type=row["event_type"],
                timestamp=_parse_datetime(row["timestamp"]),
                details=json.loads(row["details"]) if row["details"] else None,
            )


def seed_database():
    with db.atomic():
        seed_users()
        seed_urls()
        seed_events()
        _sync_sequence(User)
        _sync_sequence(Url)
        _sync_sequence(Event)
