import pytest  # noqa: F401
from uuid import UUID
from todo_bene.domain.entities.todo import Todo
from todo_bene.infrastructure.persistence.duckdb_todo_repository import DuckDBTodoRepository

def test_repository_save_and_get_by_id(tmp_path):
    # Arrange
    db_path = tmp_path / "test_todo.db"
    repository = DuckDBTodoRepository(str(db_path))
    user_id = UUID("550e8400-e29b-41d4-a716-446655440000")
    todo = Todo(title="Acheter du lait", user=user_id)

    # Act
    repository.save(todo)
    retrieved_todo = repository.get_by_id(todo.uuid)

    # Assert
    assert retrieved_todo is not None
    assert retrieved_todo.title == "Acheter du lait"
    assert retrieved_todo.user == user_id

def test_repository_preserves_priority(tmp_path):
    # Arrange
    db_path = tmp_path / "test_priority.db"
    repository = DuckDBTodoRepository(str(db_path))
    user_id = UUID("550e8400-e29b-41d4-a716-446655440000")
    todo = Todo(title="Urgent", user=user_id, priority=True)

    # Act
    repository.save(todo)
    retrieved_todo = repository.get_by_id(todo.uuid)

    # Assert
    assert retrieved_todo.priority is True

def test_repository_preserves_dates(tmp_path):
    """
    Test que le repository enregistre et restitue correctement les timestamps.
    """
    # Arrange
    db_path = tmp_path / "test_dates.db"
    repository = DuckDBTodoRepository(str(db_path))
    user_id = UUID("550e8400-e29b-41d4-a716-446655440000")
    
    # On définit des timestamps précis (ex: 1er Janvier 2025)
    start_ts = 1735689600 
    due_ts = 1735776000
    
    todo = Todo(
        title="Tâche datée", 
        user=user_id, 
        date_start=start_ts, 
        date_due=due_ts
    )

    # Act
    repository.save(todo)
    retrieved_todo = repository.get_by_id(todo.uuid)

    # Assert
    assert retrieved_todo is not None
    # L'échec se produira ici car le repo actuel ne stocke pas ces colonnes
    assert retrieved_todo.date_start == start_ts
    assert retrieved_todo.date_due == due_ts