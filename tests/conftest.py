import pytest
from uuid import uuid4
from todo_bene.infrastructure.persistence.duckdb_connection_manager import (
    DuckDBConnectionManager,
)
from todo_bene.infrastructure.persistence.duckdb_todo_repository import (
    DuckDBTodoRepository,
)
from todo_bene.infrastructure.persistence.duckdb_category_repository import (
    DuckDBCategoryRepository,
)


# ... (garde tes fixtures setup_test_env, test_config_env, user_id telles quelles)
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
    # Attention à bien vérifier le chemin du patch selon ton arborescence
    monkeypatch.setattr(
        "todo_bene.infrastructure.cli.main.get_repository", mock_get_repository
    )
    return repo
