import pytest  # noqa: F401
from uuid import uuid4
from todo_bene.application.use_cases.todo_create import TodoCreateUseCase
from todo_bene.infrastructure.persistence.memory_todo_repository import MemoryTodoRepository

def test_todo_create_use_case():
    # Arrange
    # On prépare un repo spécifique pour les todos
    todo_repo = MemoryTodoRepository()
    use_case = TodoCreateUseCase(todo_repo)
    
    user_id = uuid4()
    todo_data = {
        "title": "Apprendre la Clean Architecture",
        "user": user_id,
        "category": "travail",
        "description": "Pratiquer le TDD avec Gemini"
    }
    
    # Act
    todo = use_case.execute(**todo_data)
    
    # Assert
    assert todo.title == todo_data["title"]
    assert todo.user == user_id
    # On vérifie que le Use Case a bien demandé au repo de sauvegarder
    assert todo_repo.get_by_id(todo.uuid) == todo

def test_todo_create_root_success():
    # Arrange
    repo = MemoryTodoRepository()
    use_case = TodoCreateUseCase(repo)
    user_id = uuid4()
    
    # Act
    new_todo = use_case.execute(
        title="Acheter du pain",
        user=user_id,
        category="Courses",
        description="Au levain de préférence"
    )
    
    # Assert
    assert new_todo.user == user_id
    assert new_todo.parent is None
    assert repo.get_by_id(new_todo.uuid) is not None

def test_todo_create_child_success():
    # Arrange
    repo = MemoryTodoRepository()
    use_case = TodoCreateUseCase(repo)
    user_id = uuid4()
    
    # On crée d'abord un parent
    parent_todo = use_case.execute("Projet Vacances", user_id, "Perso", "Organiser l'été")
    
    # Act: On crée un enfant en passant l'UUID du parent
    child_todo = use_case.execute(
        title="Réserver l'hôtel",
        user=user_id,
        category="Perso",
        description="Vérifier l'annulation gratuite",
        parent=parent_todo.uuid
    )
    
    # Assert
    assert child_todo.parent == parent_todo.uuid
    assert child_todo.user == user_id

def test_todo_create_with_extra_fields():
    # Arrange
    repo = MemoryTodoRepository()
    use_case = TodoCreateUseCase(repo)
    user_id = uuid4()
    
    # Act: On teste le passage via **kwargs (ex: priority)
    todo = use_case.execute(
        "Urgent", user_id, "Test", "...", 
        priority=True,
        date_due="2026-12-31 23:59:59"
    )
    
    # Assert
    assert todo.priority is True
    # Vérifie que le __post_init__ de l'entité a bien converti la date en timestamp
    assert isinstance(todo.date_due, int)
