import pytest  # noqa: F401
from uuid import uuid4
from todo_bene.application.use_cases.todo_get import TodoGetUseCase
from todo_bene.infrastructure.persistence.memory_todo_repository import (
    MemoryTodoRepository,
)
from todo_bene.domain.entities.todo import Todo


def test_todo_get_use_case_success():
    # Arrange
    repo = MemoryTodoRepository()
    user_id = uuid4()
    # On crée et sauvegarde manuellement un Todo pour simuler une donnée existante
    existing_todo = Todo(
        title="Tâche existante",
        user=user_id,
        category="test",
        description="Une description",
    )
    repo.save(existing_todo)

    use_case = TodoGetUseCase(repo)

    # Act. _ car pas d'enfant dans ce test
    found_todo, _ = use_case.execute(existing_todo.uuid, existing_todo.user)

    # Assert
    assert found_todo is not None
    assert found_todo.uuid == existing_todo.uuid
    assert found_todo.title == "Tâche existante"


def test_todo_get_use_case_not_found():
    # Arrange
    repo = MemoryTodoRepository()
    use_case = TodoGetUseCase(repo)

    # Act
    # On explicite que même avec un user_id valide, si le Todo n'existe pas, c'est None
    found_todo, _ = use_case.execute(todo_id=uuid4(), user_id=uuid4())

    # Assert
    assert found_todo is None


def test_todo_get_with_children():
    # Arrange
    repo = MemoryTodoRepository()
    use_case = TodoGetUseCase(repo)
    user_id = uuid4()

    # Création du parent
    parent = Todo(title="Parent", user=user_id, category="test", description="...")
    repo.save(parent)

    # Création de deux enfants
    child1 = Todo(
        title="Enfant 1",
        user=user_id,
        category="test",
        description="...",
        parent=parent.uuid,
    )
    child2 = Todo(
        title="Enfant 2",
        user=user_id,
        category="test",
        description="...",
        parent=parent.uuid,
    )
    repo.save(child1)
    repo.save(child2)

    # Act
    # On s'attend à ce que le Use Case nous renvoie le Todo ET ses enfants
    result = use_case.execute(parent.uuid, user_id)

    # Assert
    todo, children = result
    assert todo.uuid == parent.uuid
    assert len(children) == 2
    # assert children[0].title == "Enfant 1"
    assert "Enfant 1" in [child.title for child in children]


def test_todo_get_fails_for_wrong_user():
    # Arrange
    repo = MemoryTodoRepository()
    use_case = TodoGetUseCase(repo)

    owner_id = uuid4()
    hacker_id = uuid4()

    # Un Todo appartenant à l'owner
    todo = Todo(
        uuid=uuid4(), title="Secret", user=owner_id, category="Work", description="..."
    )
    repo.save(todo)

    # Act
    # L'utilisateur "hacker" tente d'accéder au Todo de l'owner
    found_todo, _ = use_case.execute(todo.uuid, hacker_id)

    # Assert
    assert found_todo is None  # On refuse l'accès
