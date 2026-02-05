import pendulum
import pytest  # noqa: F401
from uuid import uuid4
from typer.testing import CliRunner
from todo_bene.infrastructure.cli.main import app
from todo_bene.domain.entities.todo import Todo

runner = CliRunner()


def test_cli_update_todo_title_and_description(
    repository, monkeypatch, test_config_env
):
    # GIVEN
    user_id = uuid4()
    # Mock de la config pour l'ID utilisateur
    monkeypatch.setattr(
        "todo_bene.infrastructure.cli.main.load_user_info",
        lambda: (user_id, "dev.db", "test_profile"),
    )

    todo = Todo(title="Initial", description="Ancienne", user=user_id)
    repository.save(todo)

    # Simulation des entrées :
    # '1' -> Choisir le Todo dans la liste
    # 'm' -> Menu modifier
    # 'Nouveau Titre' -> Pour le titre
    # 'Nouvelle Desc' -> Pour la description
    # (Cat) -> \n
    # (Priority) -> \n
    # (Start) -> \n
    # (Due) -> \n
    # 'r' -> Retour au menu principal
    inputs = "1\nm\nNouveau Titre\nNouvelle Desc\n\n\n\n\nr\n"

    # WHEN
    result = runner.invoke(
        app, ["list"], input=inputs, env={"TODO_BENE_CONFIG_PATH": str(test_config_env)}
    )

    # THEN
    updated = repository.get_by_id(todo.uuid)
    assert result.exit_code == 0
    assert updated.title == "Nouveau Titre"
    assert updated.description == "Nouvelle Desc"
    assert "mis à jour avec succès" in result.stdout


def test_cli_update_forbidden_field_feedback(repository, monkeypatch, test_config_env):
    # GIVEN
    user_id = uuid4()
    monkeypatch.setattr(
        "todo_bene.infrastructure.cli.main.load_user_info",
        lambda: (user_id, "dev.db", "test_profile"),
    )

    todo = Todo(title="Test Protec", user=user_id)
    repository.save(todo)

    # Simulation : On tente de passer 'user' dans les arguments (via un mock ou input)
    # Ici on teste surtout que si le Use Case renvoie 'user', la CLI l'affiche.
    # On va simuler l'entrée 'm', puis 'Entrée' pour titre/desc,
    # mais on va vérifier le comportement du Use Case.

    inputs = "1\nm\n\n\n\n\n\n\nr\n"

    # Comme on ne peut pas injecter 'user' facilement via Prompt.ask,
    # ce test vérifie surtout la stabilité.
    # Pour tester RÉELLEMENT le feedback forbidden, on peut mocker le retour du Use Case :

    with monkeypatch.context() as m:
        m.setattr(
            "todo_bene.application.use_cases.todo_update.TodoUpdateUseCase.execute",
            lambda *args, **kwargs: ["user", "uuid"],
        )

        result = runner.invoke(
            app,
            ["list"],
            input=inputs,
            env={"TODO_BENE_CONFIG_PATH": str(test_config_env)},
        )
        assert "Champs non modifiables : user, uuid" in result.stdout


def test_cli_update_dates_success(repository, monkeypatch, test_config_env):
    # GIVEN
    user_id = uuid4()
    monkeypatch.setattr(
        "todo_bene.infrastructure.cli.main.load_user_info",
        lambda: (user_id, "dev.db", "test_profile"),
    )

    # On crée un Todo qui commence aujourd'hui
    now = pendulum.now("UTC").start_of("minute")
    todo = Todo(title="Date Test", user=user_id, date_start=now.timestamp())
    repository.save(todo)

    # Simulation :
    future_date_str = "31/12/2026 23:59"
    # 1 -> \n m -> \n (Titre) -> \n (Desc) -> \n (Priority) -> \n (Cat) -> \n (Start) -> \n DATE (Due)
    inputs = f"1\nm\n\n\n\n\n\n{future_date_str}\nr\n"
    # WHEN
    result = runner.invoke(
        app, ["list"], input=inputs, env={"TODO_BENE_CONFIG_PATH": str(test_config_env)}
    )
    # THEN
    updated = repository.get_by_id(todo.uuid)
    assert result.exit_code == 0
    # On vérifie que le timestamp enregistré correspond à la fin d'année 2026
    tz = pendulum.local_timezone()
    expected_ts = pendulum.from_format(
        future_date_str, "DD/MM/YYYY HH:mm", tz=tz
    ).timestamp()
    assert int(updated.date_due) == int(expected_ts)


def test_cli_update_date_invalid_format_shows_error(
    repository, monkeypatch, test_config_env
):
    user_id = uuid4()
    monkeypatch.setattr(
        "todo_bene.infrastructure.cli.main.load_user_info",
        lambda: (user_id, "dev.db", "test_profile"),
    )
    todo = Todo(title="Date Fail", user=user_id)
    repository.save(todo)

    # On saisit un format invalide pour la date
    inputs = "1\nm\n\n\n\ninvalide-date\nr\n"

    # WHEN
    result = runner.invoke(
        app, ["list"], input=inputs, env={"TODO_BENE_CONFIG_PATH": str(test_config_env)}
    )

    # THEN
    # On vérifie que l'erreur de parsing est affichée à l'écran
    assert "Format de date invalide" in result.stdout
