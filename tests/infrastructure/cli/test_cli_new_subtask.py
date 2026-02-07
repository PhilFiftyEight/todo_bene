import pytest  # noqa: F401
import pendulum
from todo_bene.domain.entities.todo import Todo
from todo_bene.infrastructure.cli.main import app
from typer.testing import CliRunner

runner = CliRunner()


def test_menu_detail_trigger_new_subtask(
    repository, user_id, monkeypatch, test_config_env
):
    """
    Étape 1 : Déclenchement
    GIVEN: Un Todo parent existant dans la catégorie 'Travail'
    WHEN: L'utilisateur saisit 'n' dans le menu de détail
    THEN: Le CLI doit afficher le bandeau de création avec l'héritage visuel
    """
    # 1. Mock de la configuration pour que l'app utilise notre user_id de test
    monkeypatch.setattr(
        "todo_bene.infrastructure.cli.main.load_user_info",
        lambda: (user_id, "dev.db", "test_profile"),
    )

    # 1. Préparation du parent
    parent = Todo(
        title="Projet Alpha",
        user=user_id,
        category="Travail",
        date_start=pendulum.now().timestamp(),
        date_due=pendulum.now().add(days=1).timestamp(),
    )
    repository.save(parent)

    # 2. Simulation :
    # '1' -> sélectionne le parent dans la liste
    # 'n' -> demande une nouvelle sous-tâche
    # 'r' -> pour retourner dans la vue list
    # 'q' -> pour quitter le menu principal
    inputs = iter(["1", "n", "r", "q"])
    monkeypatch.setattr("rich.prompt.Prompt.ask", lambda prompt, **kwargs: next(inputs))

    result = runner.invoke(
        app, ["list"], env={"TODO_BENE_CONFIG_PATH": str(test_config_env)}
    )

    # 3. Assertions pour le RED
    assert "Nouvelle sous-tâche pour : Projet Alpha" in result.stdout
    assert "Catégorie héritée : Travail" in result.stdout


def test_menu_detail_inputs_subtask(repository, user_id, monkeypatch, test_config_env):
    # (Garder le même mock de load_user_info que précédemment)
    monkeypatch.setattr(
        "todo_bene.infrastructure.cli.main.load_user_info",
        lambda: (user_id, "dev.db", "test_profile"),
    )

    parent = Todo(title="Parent", user=user_id, category="Travail")
    repository.save(parent)

    # Simulation des entrées :
    # "1" -> Sélection
    # "n" -> Nouvelle sous-tâche
    # "Sous-tâche test" -> Titre
    # "Ma description" -> Description
    # "y" -> Priorité (y/n)
    # "r", "q" -> Sortie
    inputs = "1\nn\nSous-tâche test\nMa description\ny\nr\nq"
    result = runner.invoke(
        app, ["list"], input=inputs, env={"TODO_BENE_CONFIG_PATH": str(test_config_env)}
    )

    # Assertions : on vérifie que les prompts ont été affichés (ou sont présents dans le stdout)
    assert "Titre de la sous-tâche" in result.stdout
    assert "Description (optionnelle)" in result.stdout
    assert "Prioritaire ?" in result.stdout


def test_menu_detail_dates_subtask(repository, user_id, monkeypatch, test_config_env):
    monkeypatch.setattr(
        "todo_bene.infrastructure.cli.main.load_user_info",
        lambda: (user_id, "dev.db", "test_profile"),
    )

    # On fixe des dates précises pour le parent
    debut_parent = pendulum.now(tz=pendulum.local_timezone())
    fin_parent = debut_parent.add(days=2)
    fin_parent = fin_parent.at(23, 59, 59)

    parent = Todo(
        title="Parent Dates",
        user=user_id,
        category="Travail",
        date_start=int(debut_parent.timestamp()),
        date_due=int(fin_parent.timestamp()),
    )
    repository.save(parent)

    # Entrées : 1 (détail), n (sous-tâche), "Titre", "Desc", "n" (non prioritaire)
    # Puis [Enter] pour date début, [Enter] pour date fin, r (retour), q (quit)
    # inputs = "1\nn\nTitre\nDesc\nn\n\n\nr\nq\n"
    inputs = "1\nn\nTitre\nDesc\n\n\n\n\n\n"
    result = runner.invoke(
        app, ["list"], input=inputs, env={"TODO_BENE_CONFIG_PATH": str(test_config_env)}
    )

    # On vérifie que le CLI propose les dates du parent par défaut
    assert (
        f"Date de début ({debut_parent.format('DD/MM/YYYY HH:mm:ss')})" in result.stdout
    )
    assert f"Échéance ({fin_parent.format('DD/MM/YYYY HH:mm:ss')})" in result.stdout

    # test de persistance
    all_todos = repository.find_all_active_by_user(user_id)
    # On attend 2 todos : le parent et la nouvelle sous-tâche
    assert len(all_todos) == 2

    subtask = next(t for t in all_todos if t.title == "Titre")
    assert subtask.parent == parent.uuid
    assert subtask.category == "Travail"
    assert subtask.description == "Desc"
