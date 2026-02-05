import pytest  # noqa: F401
from todo_bene.domain.entities.todo import Todo
from todo_bene.application.use_cases.todo_complete import TodoCompleteUseCase
from todo_bene.infrastructure.persistence.memory.memory_todo_repository import (
    MemoryTodoRepository,
)


def test_complete_child_identifies_parent_as_pending(user_id):
    repo = MemoryTodoRepository()
    use_case = TodoCompleteUseCase(repo)

    # GIVEN : Un arbre Racine -> Parent -> Enfant
    racine = Todo(title="Racine", user=user_id)
    repo.save(racine)

    parent = Todo(title="Parent", user=user_id, parent=racine.uuid)
    repo.save(parent)

    enfant = Todo(title="Enfant", user=user_id, parent=parent.uuid)
    repo.save(enfant)

    # WHEN : On complète l'enfant (le seul fils de Parent)
    result = use_case.execute(todo_id=enfant.uuid, user_id=user_id)

    # THEN : Le Use Case doit nous dire que le Parent est maintenant prêt
    # On imagine un retour structuré du Use Case
    assert result["completed_id"] == enfant.uuid
    assert parent.uuid in result["newly_pending_ids"]
    assert result["is_root"] is False


def test_complete_child_only_signals_parent_if_all_children_done(user_id):
    repo = MemoryTodoRepository()
    use_case = TodoCompleteUseCase(repo)

    # GIVEN : Un Parent avec DEUX enfants
    parent = Todo(title="Parent", user=user_id)
    repo.save(parent)

    enfant_1 = Todo(title="Enfant 1", user=user_id, parent=parent.uuid)
    enfant_2 = Todo(title="Enfant 2", user=user_id, parent=parent.uuid)
    repo.save(enfant_1)
    repo.save(enfant_2)

    # ACTION 1 : On complète le premier enfant
    result_1 = use_case.execute(todo_id=enfant_1.uuid, user_id=user_id)

    # ASSERTION 1 : Le parent ne doit PAS être dans les "newly_pending"
    assert parent.uuid not in result_1["newly_pending_ids"]

    # ACTION 2 : On complète le deuxième (et dernier) enfant
    result_2 = use_case.execute(todo_id=enfant_2.uuid, user_id=user_id)

    # ASSERTION 2 : Là, le parent doit être signalé
    assert parent.uuid in result_2["newly_pending_ids"]


def test_complete_parent_with_active_children_fails(user_id):
    repo = MemoryTodoRepository()
    use_case = TodoCompleteUseCase(repo)

    # GIVEN : Un parent avec un enfant NON terminé
    parent = Todo(title="Parent", user=user_id)
    repo.save(parent)
    enfant = Todo(title="Enfant", user=user_id, parent=parent.uuid)
    repo.save(enfant)  # state est False par défaut

    # WHEN : On essaie de terminer le parent
    result = use_case.execute(todo_id=parent.uuid, user_id=user_id)

    # THEN : Le Use Case doit signaler que c'est impossible (ex: via un flag ou une erreur)
    assert result["success"] is False
    assert "active_children" in result["reason"]


def test_force_complete_finishes_all_descendants(user_id):
    repo = MemoryTodoRepository()
    use_case = TodoCompleteUseCase(repo)

    # GIVEN : G -> P -> E
    g = Todo(title="Grand-Parent", user=user_id)
    repo.save(g)
    p = Todo(title="Parent", user=user_id, parent=g.uuid)
    repo.save(p)
    e = Todo(title="Enfant", user=user_id, parent=p.uuid)
    repo.save(e)

    # WHEN : On force la complétude du Grand-Parent
    result = use_case.execute(todo_id=g.uuid, user_id=user_id, force=True)

    # THEN tous les descendants sont complétés
    assert result["success"] is True
    assert repo.get_by_id(g.uuid).state is True
    assert repo.get_by_id(p.uuid).state is True
    assert repo.get_by_id(e.uuid).state is True
