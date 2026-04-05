import importlib
import sys
from unittest.mock import MagicMock, patch


def _import_test_db_module():
    sys.modules.pop("app.test_db", None)
    return importlib.import_module("app.test_db")


def test_test_db_module_reports_success(capsys):
    fake_db = MagicMock()
    fake_db.get_tables.return_value = ["users", "urls"]

    with patch("peewee.PostgresqlDatabase", return_value=fake_db):
        _import_test_db_module()

    output = capsys.readouterr().out
    assert "Connected to database" in output
    assert "Tables: ['users', 'urls']" in output
    fake_db.connect.assert_called_once()
    fake_db.get_tables.assert_called_once()
    fake_db.close.assert_called_once()


def test_test_db_module_reports_failure(capsys):
    fake_db = MagicMock()
    fake_db.connect.side_effect = Exception("boom")

    with patch("peewee.PostgresqlDatabase", return_value=fake_db):
        _import_test_db_module()

    output = capsys.readouterr().out
    assert "Connection failed" in output
    assert "boom" in output
    fake_db.connect.assert_called_once()
    fake_db.get_tables.assert_not_called()
    fake_db.close.assert_not_called()