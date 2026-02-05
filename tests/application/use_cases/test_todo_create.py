import pendulum
import pytest  # noqa: F401
from uuid import uuid4
from todo_bene.application.use_cases.todo_create import TodoCreateUseCase
from todo_bene.infrastructure.persistence.memory_todo_repository import (
    MemoryTodoRepository,
)
from todo_bene.domain.entities.category import Category


def test_todo_create_use_case():
    # Arrange
    # On prépare un repo spécifique pour les todos
    repo = MemoryTodoRepository()
    use_case = TodoCreateUseCase(repo)

    user_id = uuid4()
    todo_data = {
        "title": "Apprendre la Clean Architecture",
        "user": user_id,
        "category": Category.TRAVAIL,
        "description": "Pratiquer le TDD avec Gemini",
    }

    # Act
    todo = use_case.execute(**todo_data)

    # Assert
    assert todo.title == todo_data["title"]
    assert todo.user == user_id
    # On vérifie que le Use Case a bien demandé au repo de sauvegarder
    assert repo.get_by_id(todo.uuid) == todo


def test_todo_create_root_success():
    # Arrange
    repo = MemoryTodoRepository()
    use_case = TodoCreateUseCase(repo)
    user_id = uuid4()

    # Act
    new_todo = use_case.execute(
        title="Acheter du pain",
        user=user_id,
        category=Category.QUOTIDIEN,
        description="Au levain de préférence",
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
    parent_todo = use_case.execute(
        "Projet Vacances", user_id, Category.QUOTIDIEN, "Organiser l'été"
    )

    # Act: On crée un enfant en passant l'UUID du parent
    child_todo = use_case.execute(
        title="Réserver l'hôtel",
        user=user_id,
        category=Category.LOISIRS,
        description="Vérifier l'annulation gratuite",
        parent=parent_todo.uuid,
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
        "Urgent",
        user_id,
        Category.TRAVAIL,
        "...",
        priority=True,
        date_due="2026-12-31 23:59:59",
    )

    # Assert
    assert todo.priority is True
    # Vérifie que le __post_init__ de l'entité a bien converti la date en timestamp
    assert isinstance(todo.date_due, int)


def test_create_todo_with_parent_success(user_id):
    # GIVEN
    repo = MemoryTodoRepository()
    use_case = TodoCreateUseCase(repo)
    # On crée d'abord un parent en base avec une date lointaine
    repo.save(
        repo._row_to_todo(
            [
                uuid4(),
                "Parent",
                "",
                "",
                False,
                False,
                1000,
                9999999999,
                user_id,
                None,
            ]
        )
    )
    # Récupérons l'ID généré ou injecté
    parent_id = repo.find_top_level_by_user(user_id)[0].uuid

    # WHEN
    new_todo = use_case.execute(title="Sous-tâche", user=user_id, parent=parent_id)

    # THEN
    assert new_todo.parent == parent_id
    saved_todo = repo.get_by_id(new_todo.uuid)
    assert saved_todo.parent == parent_id


def test_create_todo_with_parent_date_error(user_id):
    # GIVEN
    repo = MemoryTodoRepository()
    use_case = TodoCreateUseCase(repo)
    # On crée un parent qui finit très tôt (timestamp 1000)
    parent_id = uuid4()
    # import todo_bene.domain.entities.todo as todo_mod
    from todo_bene.domain.entities.todo import Todo

    p = Todo(title="Parent", user=user_id, uuid=parent_id, date_due=1000)
    repo.save(p)

    # WHEN / THEN : On essaie de créer un enfant qui finit demain
    # Cela doit lever une ValueError à cause de ta règle n°2 dans le Use Case
    with pytest.raises(
        ValueError,
        match="La date d'échéance de l'enfant ne peut pas dépasser celle du parent",
    ):
        use_case.execute(
            title="Sous-tâche trop longue",
            user=user_id,
            parent=parent_id,
            date_due="31/12/2099",
        )


def test_todo_create_assigns_default_category_if_none():
    # GIVEN
    repo = MemoryTodoRepository()
    use_case = TodoCreateUseCase(repo)
    user_id = uuid4()

    # WHEN: Quand category n'est pas donné
    todo = use_case.execute(title="Test défaut", user=user_id)

    # THEN: On vérifie que c'est "Quotidien" (via la constante de l'entité)
    assert todo.category == Category.QUOTIDIEN


def test_root_todo_cannot_start_in_the_past(user_id):
    """
    Une tâche racine ne peut pas commencer dans le passé.
    """
    repo = MemoryTodoRepository()

    use_case = TodoCreateUseCase(repo)

    # Date yesterday
    past_date = pendulum.now().subtract(days=1).format("DD/MM/YYYY")

    with pytest.raises(
        ValueError, match="Une tâche racine ne peut pas commencer dans le passé"
    ):
        use_case.execute(title="Tâche fantôme", user=user_id, date_start=past_date)
