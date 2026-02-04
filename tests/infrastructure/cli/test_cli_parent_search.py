import pytest  # noqa: F401
from typer.testing import CliRunner
from todo_bene.infrastructure.cli.main import app
from todo_bene.domain.entities.todo import Todo

runner = CliRunner()


def test_create_todo_with_interactive_parent_selection(
    repository, user_id, monkeypatch, test_config_env
):
    # 1. On force le CLI à utiliser l'user de test
    monkeypatch.setattr(
        "todo_bene.infrastructure.cli.main.load_user_info", lambda: (user_id, "dev.db", "test_profile")
    )

    # 2. GIVEN: Deux parents potentiels en base
    repository.save(Todo(title="Projet Alpha", user=user_id))
    repository.save(Todo(title="Projet Beta", user=user_id))

    # 3. WHEN: On simule l'entrée "1" pour choisir "Projet Alpha"
    # Note: On ajoute \n pour valider le choix
    result = runner.invoke(
        app, ["add", "Sous-tâche", "--parent", "Projet"], input="1\n",env={"TODO_BENE_CONFIG_PATH": str(test_config_env)}
    )

    # 4. THEN
    if result.exit_code != 0:
        print(result.stdout)

    assert result.exit_code == 0
    assert "Plusieurs parents possibles" in result.stdout
    assert "Projet Alpha" in result.stdout
    assert "Succès" in result.stdout

    # 5. Vérification finale en base
    # On cherche la sous-tâche pour voir si elle a bien le parent
    results = repository.search_by_title(user_id, "Sous-tâche")
    assert len(results) == 1
    assert results[0].parent is not None

    # On vérifie que c'est bien l'UUID de Projet Alpha
    alpha = repository.search_by_title(user_id, "Alpha")[0]
    assert results[0].parent == alpha.uuid
