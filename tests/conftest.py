import pytest
import keyring
from keyring.backends.null import Keyring
from uuid import uuid4
from prompt_toolkit import PromptSession

from todo_bene.infrastructure.persistence.duckdb.duckdb_connection_manager import (
    DuckDBConnectionManager,
)
from todo_bene.infrastructure.persistence.duckdb.duckdb_todo_repository import (
    DuckDBTodoRepository,
)
from todo_bene.infrastructure.persistence.duckdb.duckdb_category_repository import (
    DuckDBCategoryRepository,
)


class MockKeyring(Keyring):
    """Un backend de stockage en mémoire pour les tests."""
    priority = 1
    def __init__(self):
        self.passwords = {}

    def get_password(self, service, username):
        return self.passwords.get(f"{service}:{username}")

    def set_password(self, service, username, password):
        self.passwords[f"{service}:{username}"] = password

    def delete_password(self, service, username):
        self.passwords.pop(f"{service}:{username}", None)

@pytest.fixture(autouse=True)
def mock_keyring_storage():
    """Active le mock keyring automatiquement pour tous les tests."""
    original_backend = keyring.get_keyring()
    keyring.set_keyring(MockKeyring())
    yield
    keyring.set_keyring(original_backend)


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


@pytest.fixture
def db_manager():
    """Gère la connexion DuckDB pour les tests (en mémoire)."""
    # On utilise :memory: pour que les tests soient rapides et isolés
    manager = DuckDBConnectionManager(":memory:")
    yield manager
    manager.close()


@pytest.fixture
def repo(db_manager):
    """Fixture pour le DuckDBTodoRepository (utilisée par les tests d'intégration)."""
    return DuckDBTodoRepository(db_manager.get_connection())


@pytest.fixture
def category_repo(db_manager):
    """Nouvelle fixture pour tester le DuckDBCategoryRepository."""
    return DuckDBCategoryRepository(db_manager.get_connection())


@pytest.fixture
def repository(monkeypatch, repo):
    """
    Assure la compatibilité avec le code de la CLI qui utilise 'with get_repository()'.
    """
    from contextlib import contextmanager

    @contextmanager
    def mock_get_repository():
        yield repo

    # On patche l'endroit où la CLI va chercher son repository
    # Attention à bien vérifier le chemin du patch l'arborescence
    monkeypatch.setattr(
        "todo_bene.infrastructure.cli.main.get_repository", mock_get_repository
    )
    return repo


@pytest.fixture
def mock_prompt_session(monkeypatch):
    """Fixture pour simuler les saisies interactives de prompt-toolkit.
    # On remplace la méthode prompt de PromptSession par un simple input()
    # pour matcher la signature complexe de prompt-toolkit.
    # On intercepte 'default' pour simuler le comportement de prompt-toolkit"""
    def _mock_prompt(*args, **kwargs):
        user_input = input()
        # Simule le comportement du paramètre 'default' de prompt-toolkit
        if not user_input and "default" in kwargs:
            return kwargs["default"]
        return user_input

    monkeypatch.setattr(PromptSession, "prompt", _mock_prompt)
    return _mock_prompt