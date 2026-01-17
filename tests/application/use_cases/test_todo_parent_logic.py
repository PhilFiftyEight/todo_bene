import pytest

# import pendulum
from uuid import uuid4
from todo_bene.application.use_cases.todo_create import TodoCreateUseCase
# from todo_bene.domain.entities.todo import Todo


def test_child_cannot_end_after_parent(test_config_env, monkeypatch):
    """
    Règle 1 : L'enfant ne peut pas finir après le parent.
    """
    from todo_bene.infrastructure.cli.main import get_repository

    repo = get_repository()
    use_case = TodoCreateUseCase(repo)
    user_id = uuid4()

    # 1. Créer un parent qui finit le 15 Janvier
    parent = use_case.execute(title="Parent", user=user_id, date_due="15/01/2026")

    # 2. Tenter de créer un enfant qui finit le 20 Janvier (DOIT LEVER UNE ERREUR)
    with pytest.raises(
        ValueError,
        match="La date d'échéance de l'enfant ne peut pas dépasser celle du parent",
    ):
        use_case.execute(
            title="Enfant rebelle",
            user=user_id,
            parent=parent.uuid,
            date_due="20/01/2026",
        )


def test_multi_generational_children(test_config_env):
    """
    Règle 2 : Un enfant peut avoir des enfants (Sous-sous-tâche).
    """
    from todo_bene.infrastructure.cli.main import get_repository

    repo = get_repository()
    use_case = TodoCreateUseCase(repo)
    user_id = uuid4()

    parent = use_case.execute(title="Grand-parent", user=user_id)
    enfant = use_case.execute(title="Enfant", user=user_id, parent=parent.uuid)
    petit_enfant = use_case.execute(
        title="Petit-enfant", user=user_id, parent=enfant.uuid
    )

    assert petit_enfant.parent == enfant.uuid
    assert enfant.parent == parent.uuid
