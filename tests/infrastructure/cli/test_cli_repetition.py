import pytest
import pendulum
from typer.testing import CliRunner
from todo_bene.infrastructure.cli.main import app
from todo_bene.infrastructure.persistence.memory.memory_todo_repository import MemoryTodoRepository
from todo_bene.domain.entities.todo import Todo

runner = CliRunner()

def test_cli_integration_repetition_flow(monkeypatch,user_id, repository, test_config_env):
    """
    TEST (RED) : Intégration complète via la commande list.
    Saisie de la fréquence lors de la complétion et vérification de la répétition.
    """
    # On mocke load_user_info PARTOUT où il est utilisé dans main
    monkeypatch.setattr(
        "todo_bene.infrastructure.cli.main.load_user_info",
        lambda: (user_id, "dev.db", "test_profile"),
    )
    # GIVEN : Une tâche racine sans fréquence
    tz = pendulum.local_timezone()
    todo = Todo(
        title="Aller courir",
        user=user_id,
        state=False,
        date_start=pendulum.now(tz=tz).int_timestamp
    )
    repository.save(todo)

    # Simulation des entrées :
    # 1 -> Sélectionne le todo
    # t -> Terminer
    # o -> "Voulez-vous la répéter ?" -> OUI (C'est ce qui manquait)
    # tous les jours -> "Fréquence de répétition ?"
    # r -> Retour
    inputs = "1\nt\no\ntous les jours\nr\n"

    # WHEN
    result = runner.invoke(app, ["list"], input=inputs, env={"TODO_BENE_CONFIG_PATH": str(test_config_env)})

    # EXPECTED
    # 1. Vérifie que la question de répétition a été posée
    assert "Voulez-vous la répéter" in result.output
    # 2. Vérifie que le prompt de fréquence est apparu suite au 'o'
    assert "Fréquence de répétition" in result.output
    
    assert len(list(repository.find_top_level_by_user(user_id))) == 365