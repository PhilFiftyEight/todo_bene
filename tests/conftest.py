import pytest
#import os

@pytest.fixture(autouse=True)
def setup_test_env(tmp_path, monkeypatch):
    """Isole totalement la config et la DB pour chaque test."""
    fake_config = tmp_path / ".todo_bene.json"
    fake_db = tmp_path / "test_todo_bene.db"

    # On injecte les chemins dans l'environnement AVANT que les tests ne tournent
    monkeypatch.setenv("TODO_BENE_CONFIG_PATH", str(fake_config))
    monkeypatch.setenv("TODO_BENE_DB_PATH", str(fake_db))

    return {
        "config": fake_config,
        "db": fake_db
    }

@pytest.fixture
def test_config_env(setup_test_env):
    """Alias pour les anciens tests qui attendent un objet Path."""
    return setup_test_env["config"]
