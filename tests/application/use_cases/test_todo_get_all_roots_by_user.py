import pytest  # noqa: F401
from uuid import uuid4
from todo_bene.domain.entities.todo import Todo
from todo_bene.infrastructure.persistence.memory_todo_repository import MemoryTodoRepository
from todo_bene.application.use_cases.todo_get_all_roots_by_user import TodoGetAllRootsByUserUseCase

def test_todo_get_all_roots_by_user_success():
    # Arrange
    repo = MemoryTodoRepository()
    use_case = TodoGetAllRootsByUserUseCase(repo)
    
    user_id = uuid4()
    other_user_id = uuid4()
    
    # 1. Un todo racine pour notre utilisateur (doit être trouvé)
    root_todo = Todo(uuid=uuid4(), title="Root User A", user=user_id, category="travail", description="...")
    repo.save(root_todo)
    
    # 2. Un todo enfant pour notre utilisateur (ne doit PAS être trouvé)
    child_todo = Todo(uuid=uuid4(), title="Child User A", user=user_id, parent=root_todo.uuid, category="travail", description="...")
    repo.save(child_todo)
    
    # 3. Un todo racine pour un AUTRE utilisateur (ne doit PAS être trouvé)
    other_todo = Todo(uuid=uuid4(), title="Root User B", user=other_user_id, category="travail", description="...")
    repo.save(other_todo)

    # Act
    found_todos = use_case.execute(user_id)

    # Assert
    assert len(found_todos) == 1
    assert found_todos[0].uuid == root_todo.uuid
    assert found_todos[0].user == user_id
    assert found_todos[0].parent is None

def test_todo_get_all_roots_by_user_empty_when_none():
    # Arrange
    repo = MemoryTodoRepository()
    use_case = TodoGetAllRootsByUserUseCase(repo)
    user_id = uuid4()

    # Act
    found_todos = use_case.execute(user_id)

    # Assert
    assert found_todos == []