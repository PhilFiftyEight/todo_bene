import pendulum
import pytest
from todo_bene.application.use_cases.todo_create import TodoCreateUseCase
from todo_bene.domain.entities.todo import Todo
from todo_bene.infrastructure.persistence.memory.memory_todo_repository import (
    MemoryTodoRepository,
)


def test_child_cannot_end_after_parent(user_id):
    # GIVEN
    repo = MemoryTodoRepository()
    use_case = TodoCreateUseCase(repo)

    # Utiliser une date dans le futur (ex: dans 10 jours)
    future_date = pendulum.now().add(days=10).format("DD/MM/YYYY")

    # Créer un parent qui finit dans 10 jours
    parent = use_case.execute(title="Parent", user=user_id, date_due=future_date)

    # Tenter de créer un enfant qui finit après (J+11)
    too_late = pendulum.now().add(days=11).format("DD/MM/YYYY")

    with pytest.raises(
        ValueError,
        match=r"La date d'échéance de l'enfant ne peut pas dépasser celle du parent\.",
    ):
        use_case.execute(
            title="Enfant rebelle",
            user=user_id,
            parent=parent.uuid,
            date_due=too_late,
        )


def test_multi_generational_children(user_id):
    """
    Règle: Un enfant peut avoir des enfants (Sous-sous-tâche).
    """
    repo = MemoryTodoRepository()
    use_case = TodoCreateUseCase(repo)

    parent = use_case.execute(title="Grand-parent", user=user_id)
    enfant = use_case.execute(title="Enfant", user=user_id, parent=parent.uuid)
    petit_enfant = use_case.execute(
        title="Petit-enfant", user=user_id, parent=enfant.uuid
    )

    assert petit_enfant.parent == enfant.uuid
    assert enfant.parent == parent.uuid


def test_child_inherits_parent_start_date_by_default(user_id):
    """
    Règle: Si aucune date de début n'est fournie,
    l'enfant hérite de celle du parent.
    """
    repo = MemoryTodoRepository()
    use_case = TodoCreateUseCase(repo)

    # Parent commençant dans 5 jours
    parent_start = pendulum.now().add(days=5).format("DD/MM/YYYY HH:mm")
    parent = use_case.execute(
        title="Parent futur", user=user_id, date_start=parent_start
    )

    # Enfant créé sans date_start
    child = use_case.execute(
        title="Enfant automatique", user=user_id, parent=parent.uuid
    )

    # L'enfant doit avoir hérité de la date exacte du parent
    assert child.date_start == parent.date_start


def test_child_start_date_cannot_be_before_parent_start_date(user_id):
    """
    Règle: Si une date est fournie pour l'enfant,
    elle ne peut pas être antérieure à celle du parent.
    """
    repo = MemoryTodoRepository()
    use_case = TodoCreateUseCase(repo)

    # Parent commençant dans 10 jours
    parent_start_dt = pendulum.now().add(days=10)
    parent = use_case.execute(
        title="Parent",
        user=user_id,
        date_start=parent_start_dt.format("DD/MM/YYYY HH:mm"),
    )

    # Tentative de créer un enfant commençant 2 jours AVANT le parent (soit J+8)
    invalid_child_start = parent_start_dt.subtract(days=2).format("DD/MM/YYYY HH:mm")

    with pytest.raises(
        ValueError,
        match="La date de début de l'enfant ne peut pas être antérieure à celle du parent",
    ):
        use_case.execute(
            title="Enfant prématuré",
            user=user_id,
            parent=parent.uuid,
            date_start=invalid_child_start,
        )


def test_create_child_forces_parent_category(repository, user_id):
    """
    Comportement attendu :
    Le Use Case doit ignorer la catégorie fournie si un parent est spécifié
    et forcer l'héritage de la catégorie du parent.
    """
    # GIVEN : Un parent dans 'Travail'
    # On utilise des dates formatées comme attendu par le Use Case
    date_start_str = "2026-02-01 08:00"
    date_due_str = "2026-02-01 18:00"

    parent = Todo(
        title="Parent",
        user=user_id,
        category="Travail",
        # date_start=pendulum.parse(date_start_str).timestamp(),
        # date_due=pendulum.parse(date_due_str).timestamp()
        date_start=date_start_str,
        date_due=date_due_str,
    )
    repository.save(parent)

    use_case = TodoCreateUseCase(repository)

    # WHEN : On tente l'injection d'une catégorie différente
    child = use_case.execute(
        user=user_id,  # Argument correct : 'user' et non 'user_id'
        title="Enfant",
        category="Personnel",  # Devrait être ignoré
        parent=parent.uuid,
        date_start=date_start_str,
        date_due=date_due_str,
    )

    # THEN : L'assertion échouera car le Use Case prendra 'Personnel' pour l'instant
    assert child.category == "Travail"
    assert repository.get_by_id(child.uuid).category == "Travail"
