from uuid import uuid4
from todo_bene.domain.entities.todo import Todo
from todo_bene.infrastructure.cli.main import app
from typer.testing import CliRunner

runner = CliRunner()


def test_cli_terminer_change_state_in_db(monkeypatch, repository, test_config_env):
    # GIVEN
    user_id = uuid4()
    # 1. On mocke load_user_info PARTOUT où il est utilisé dans main
    monkeypatch.setattr(
        "todo_bene.infrastructure.cli.main.load_user_info",
        lambda: (user_id, "dev.db", "test_profile"),
    )

    todo = Todo(title="Tâche à finir", user=user_id)
    repository.save(todo)

    # On simule les entrées :
    # 1 (sélection)
    # t (terminer)
    # n (réponse à la question de répétition)
    # r (retour si jamais le return ne s'exécute pas)
    # WHEN
    result = runner.invoke(
        app,
        ["list"],
        input="1\nt\nn\nr\n",
        env={"TODO_BENE_CONFIG_PATH": str(test_config_env)},
    )

    # THEN
    # On force une relecture propre depuis le repository
    updated_todo = repository.get_by_id(todo.uuid)

    assert updated_todo.state is True
    # On vérifie aussi que le message de succès est apparu dans la console
    assert "terminée" in result.stdout.lower()


def test_cli_proposes_force_complete_when_children_active(
    repository, monkeypatch, test_config_env
):
    # GIVEN
    user_id = uuid4()
    monkeypatch.setattr(
        "todo_bene.infrastructure.cli.main.load_user_info",
        lambda: (user_id, "dev.db", "test_profile"),
    )

    p = Todo(title="Parent Bloqué", user=user_id)
    repository.save(p)
    e = Todo(title="Enfant Actif", user=user_id, parent=p.uuid)
    repository.save(e)

    # Simulation :
    # '1' -> Choisir le Parent
    # 't' -> Terminer
    # 'y' -> Accepter de "Tout terminer" (force=True)
    inputs = "1\nt\ny\n"

    # WHEN
    result = runner.invoke(
        app, ["list"], input=inputs, env={"TODO_BENE_CONFIG_PATH": str(test_config_env)}
    )

    # THEN
    assert "⚠ Blocage :" in result.stdout
    assert "Voulez-vous TOUT terminer (enfants inclus) ?" in result.stdout

    # Vérification que TOUT est terminé en base
    assert repository.get_by_id(p.uuid).state is True
    assert repository.get_by_id(e.uuid).state is True
    assert "terminée !" in result.stdout.lower()
