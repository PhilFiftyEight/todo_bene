import pytest  # noqa: F401
from typer.testing import CliRunner
from todo_bene.infrastructure.cli.main import app
from todo_bene.domain.entities.todo import Todo

runner = CliRunner()


def test_cli_delete_todo_interactive(repository, user_id, monkeypatch, test_config_env):
    # 1. Mocking
    monkeypatch.setattr(
        "todo_bene.infrastructure.cli.main.load_user_info",
        lambda: (user_id, "dev.db", "test_profile"),
    )

    # 2. GIVEN: Un Todo en base
    todo = Todo(title="Tâche à supprimer", user=user_id)
    repository.save(todo)

    # 3. WHEN: On liste, on entre dans les détails (1), et on supprime (s)
    # On simule les entrées : "1" (choisir le premier), puis "s" (supprimer)
    result = runner.invoke(
        app,
        ["list"],
        input="1\ns\ny\n",
        env={"TODO_BENE_CONFIG_PATH": str(test_config_env)},
    )

    # 4. THEN
    assert result.exit_code == 0
    assert "Supprimé avec succès." in result.stdout
    assert repository.get_by_id(todo.uuid) is None
