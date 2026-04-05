import csv
import json
from datetime import datetime
from pathlib import Path

from app.database import db
from app.models.events import Event
from app.models.urls import Url
from app.models.users import User


SEED_DIR = Path(__file__).resolve().parent
SEED_LOCK_KEY = 913_004_227


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
    users_to_create = []

    with (SEED_DIR / "users.csv").open(newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            users_to_create.append(
                {
                    "id": int(row["id"]),
                    "name": row["username"],
                    "email": row["email"],
                    "password_hash": row["username"],
                    "created_at": _parse_datetime(row["created_at"]),
                }
            )

    if users_to_create:
        User.insert_many(users_to_create).on_conflict_ignore().execute()


def seed_urls():
    urls_to_create = []

    with (SEED_DIR / "urls.csv").open(newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            urls_to_create.append(
                {
                    "id": int(row["id"]),
                    "user_id": str(row["user_id"]) if row["user_id"] else None,
                    "shortcode": row["short_code"],
                    "original_url": row["original_url"],
                    "title": row["title"] or None,
                    "is_active": _parse_bool(row["is_active"]),
                    "created_at": _parse_datetime(row["created_at"]),
                    "updated_at": _parse_datetime(row["updated_at"]),
                }
            )

    if urls_to_create:
        Url.insert_many(urls_to_create).on_conflict_ignore().execute()


def seed_events():
    events_to_create = []

    with (SEED_DIR / "events.csv").open(newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            events_to_create.append(
                {
                    "id": int(row["id"]),
                    "url_id": str(row["url_id"]),
                    "user_id": str(row["user_id"]) if row["user_id"] else None,
                    "event_type": row["event_type"],
                    "timestamp": _parse_datetime(row["timestamp"]),
                    "details": json.loads(row["details"]) if row["details"] else None,
                }
            )

    if events_to_create:
        Event.insert_many(events_to_create).on_conflict_ignore().execute()


def _acquire_seed_lock():
    cursor = db.execute_sql("SELECT pg_try_advisory_lock(%s)", (SEED_LOCK_KEY,))
    row = cursor.fetchone()
    return bool(row and row[0])


def _release_seed_lock():
    db.execute_sql("SELECT pg_advisory_unlock(%s)", (SEED_LOCK_KEY,))


def seed_database():
    with db.atomic():
        if not _acquire_seed_lock():
            return

        try:
            seed_users()
            seed_urls()
            seed_events()
            _sync_sequence(User)
            _sync_sequence(Url)
            _sync_sequence(Event)
        finally:
            _release_seed_lock()
