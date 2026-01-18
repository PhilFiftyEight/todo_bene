from contextlib import contextmanager
import pytest
from uuid import uuid4
from todo_bene.infrastructure.persistence.duckdb_todo_repository import (
    DuckDBTodoRepository,
)

# import os


@pytest.fixture(autouse=True)
def setup_test_env(tmp_path, monkeypatch):
    """Isole totalement la config et la DB pour chaque test."""
    fake_config = tmp_path / ".todo_bene.json"
    fake_db = tmp_path / "test_todo_bene.db"

    # On injecte les chemins dans l'environnement AVANT que les tests ne tournent
    monkeypatch.setenv("TODO_BENE_CONFIG_PATH", str(fake_config))
    monkeypatch.setenv("TODO_BENE_DB_PATH", str(fake_db))

    return {"config": fake_config, "db": fake_db}


@pytest.fixture
def test_config_env(setup_test_env):
    """Alias pour les anciens tests qui attendent un objet Path."""
    return setup_test_env["config"]


@pytest.fixture
def user_id():
    """Génère un UUID unique pour l'utilisateur du test."""
    return uuid4()


# @pytest.fixture
# def repository():
#     """Initialise un repository en mémoire pour les tests."""
#     return DuckDBTodoRepository(db_path=":memory:")
@pytest.fixture
def repo():
    """Initialise un repository DuckDB en mémoire pour les tests."""
    # On crée l'instance manuellement pour le test
    repo = DuckDBTodoRepository(db_path=":memory:")
    yield repo  # Le test utilise le repo ici
    repo.close()  # Pytest exécute ceci APRÈS le test


@pytest.fixture
def repository(monkeypatch, repo):
    """
    Automatise le monkeypatch du repository pour la CLI.
    Utilise 'repository' (la fixture existante) et la rend compatible
    avec le pattern 'with get_repository()'.
    """

    @contextmanager
    def _mock_context():
        yield repo

    monkeypatch.setattr(
        "todo_bene.infrastructure.cli.main.get_repository", _mock_context
    )
    return repo
