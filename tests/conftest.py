"""Every test gets its own empty database and no Claude API key, so tests never touch bakaya.db or call the API."""
import pytest

import db
import seed as seed_module


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    db.init()


@pytest.fixture
def seeded():
    """The demo data, dated from today, as db.load_all() returns it."""
    seed_module.seed()
    return db.load_all()
