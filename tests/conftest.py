import os
import subprocess
import sys
import time
from pathlib import Path

import psycopg2
import pytest


# Import project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from app import create_app
from app.database import db


DOCKER_COMPOSE_FILE = PROJECT_ROOT / "docker-compose.yml"


def _run_compose_command(*args):
    subprocess.run(
        ["docker", "compose", "-f", str(DOCKER_COMPOSE_FILE), *args],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


def _get_postgres_mapped_port():
    result = subprocess.run(
        ["docker", "compose", "-f", str(DOCKER_COMPOSE_FILE), "port", "postgres", "5432"],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    mapping = result.stdout.strip().splitlines()[-1]
    return int(mapping.rsplit(":", 1)[-1])


def _wait_for_postgres(host, port, database, user, password, timeout_seconds=90):
    deadline = time.time() + timeout_seconds
    last_error = None

    while time.time() < deadline:
        try:
            conn = psycopg2.connect(
                dbname=database,
                user=user,
                password=password,
                host=host,
                port=port,
                connect_timeout=2,
            )
            conn.close()
            return
        except Exception as exc:
            last_error = exc
            time.sleep(1)

    raise RuntimeError(
        f"Postgres did not become ready within {timeout_seconds}s. Last error: {last_error}"
    )


@pytest.fixture(scope="session")
def postgres_service():
    os.environ["DATABASE_NAME"] = "hackathon_db"
    os.environ["DATABASE_HOST"] = "127.0.0.1"
    os.environ["DATABASE_USER"] = "postgres"
    os.environ["DATABASE_PASSWORD"] = "postgres"

    try:
        _run_compose_command("up", "-d", "postgres")
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            "Failed to start postgres with docker compose. "
            f"stdout={exc.stdout} stderr={exc.stderr}"
        ) from exc

    try:
        os.environ["DATABASE_PORT"] = str(_get_postgres_mapped_port())
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            "Failed to resolve mapped postgres port. "
            f"stdout={exc.stdout} stderr={exc.stderr}"
        ) from exc

    _wait_for_postgres(
        host=os.environ["DATABASE_HOST"],
        port=int(os.environ["DATABASE_PORT"]),
        database=os.environ["DATABASE_NAME"],
        user=os.environ["DATABASE_USER"],
        password=os.environ["DATABASE_PASSWORD"],
    )

    yield


@pytest.fixture()
def client(postgres_service):
    app = create_app(seed_data=False)
    app.config["TESTING"] = True

    with app.app_context():
        with db.connection_context():
            db.execute_sql("TRUNCATE TABLE events, urls, users RESTART IDENTITY CASCADE;")

    with app.test_client() as test_client:
        yield test_client

    with app.app_context():
        with db.connection_context():
            db.execute_sql("TRUNCATE TABLE events, urls, users RESTART IDENTITY CASCADE;")