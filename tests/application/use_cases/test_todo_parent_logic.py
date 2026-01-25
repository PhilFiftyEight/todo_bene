import pendulum
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

    # repo = get_repository()
    with get_repository() as repo:
        use_case = TodoCreateUseCase(repo)
        user_id = uuid4()

        # 1. Créer un parent qui finit le 15 Janvier
        parent = use_case.execute(
            title="Parent", user=user_id, date_start="15/01/2026", date_due="15/01/2026"
        )
        # 2. Tenter de créer un enfant qui finit le 20 Janvier (DOIT LEVER UNE ERREUR)
        with pytest.raises(
            ValueError,
            match=r"La date d'échéance de l'enfant ne peut pas dépasser celle du parent\.",
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

    # repo = get_repository()
    with get_repository() as repo:
        use_case = TodoCreateUseCase(repo)
        user_id = uuid4()

        parent = use_case.execute(title="Grand-parent", user=user_id)
        enfant = use_case.execute(title="Enfant", user=user_id, parent=parent.uuid)
        petit_enfant = use_case.execute(
            title="Petit-enfant", user=user_id, parent=enfant.uuid
        )

        assert petit_enfant.parent == enfant.uuid
        assert enfant.parent == parent.uuid


def test_child_inherits_parent_start_date_by_default(test_config_env):
    """
    Règle: Si aucune date de début n'est fournie, 
    l'enfant hérite de celle du parent.
    """
    from todo_bene.infrastructure.cli.main import get_repository

    with get_repository() as repo:
        use_case = TodoCreateUseCase(repo)
        user_id = uuid4()
        
        # Parent commençant dans 5 jours
        parent_start = pendulum.now().add(days=5).format("DD/MM/YYYY HH:mm")
        parent = use_case.execute(
            title="Parent futur", 
            user=user_id, 
            date_start=parent_start
        )
        
        # Enfant créé sans date_start
        child = use_case.execute(
            title="Enfant automatique", 
            user=user_id, 
            parent=parent.uuid
        )
        
        # L'enfant doit avoir hérité de la date exacte du parent
        assert child.date_start == parent.date_start

def test_child_start_date_cannot_be_before_parent_start_date(test_config_env):
    """
    Règle: Si une date est fournie pour l'enfant, 
    elle ne peut pas être antérieure à celle du parent.
    """
    from todo_bene.infrastructure.cli.main import get_repository

    with get_repository() as repo:
        use_case = TodoCreateUseCase(repo)
        user_id = uuid4()
        
        # Parent commençant dans 10 jours
        parent_start_dt = pendulum.now().add(days=10)
        parent = use_case.execute(
            title="Parent", 
            user=user_id, 
            date_start=parent_start_dt.format("DD/MM/YYYY HH:mm")
        )
        
        # Tentative de créer un enfant commençant 2 jours AVANT le parent (soit J+8)
        invalid_child_start = parent_start_dt.subtract(days=2).format("DD/MM/YYYY HH:mm")
        
        with pytest.raises(
            ValueError, 
            match="La date de début de l'enfant ne peut pas être antérieure à celle du parent"
        ):
            use_case.execute(
                title="Enfant prématuré",
                user=user_id,
                parent=parent.uuid,
                date_start=invalid_child_start
            )