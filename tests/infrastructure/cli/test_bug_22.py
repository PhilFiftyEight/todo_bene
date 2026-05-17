import pytest
from typer.testing import CliRunner
from todo_bene.infrastructure.cli.main import app
from todo_bene.infrastructure.config import save_user_config
from todo_bene.domain.entities.todo import Todo

runner = CliRunner()


def test_cli_save_category_when_create( monkeypatch, mock_prompt_session, category_repo, repository, test_config_env, user_id):
    """Verify that a category is saved when it is created."""

    monkeypatch.setattr(
        "todo_bene.infrastructure.cli.main.load_user_info",
        lambda: (user_id, "dev.db", "test_profile"),
    )
    
    # 1: with add command
    # Inputs :
    # y -> confirme la création
    inputs = "y\n"
    runner.invoke(
        app,
        ["add", "Todo test", "-c", "Nouvelle"], input=inputs,
        env={"TODO_BENE_CONFIG_PATH": str(test_config_env)},
    )    
    assert category_repo.category_exists("Nouvelle", user_id) is True

    # Second: with 'm' option in show_details view
    # Inputs :
    # 1 -> choix du todo
    # m -> menu modifier
    # \n\n\n -> titre, desc, priorité inchangés
    # Modifié -> saisie nouvelle catégorie
    # y -> confirme la création
    # \n\n -> dates inchangées
    # r -> retour
    # q -> quitter
    #inputs = "1\nm\n\n\n\nModifié\ny\n\n\n\nr\nq\n"
    inputs = "1\nm\n\n\n\nModifié\ny\n\n\n\n\n\n"
    runner.invoke(
        app,
        ["list"], input=inputs,
        env={"TODO_BENE_CONFIG_PATH": str(test_config_env)},
    )
    assert category_repo.category_exists("Modifié", user_id) is True
