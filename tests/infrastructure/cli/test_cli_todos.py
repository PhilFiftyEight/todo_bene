import os
import pendulum
import pytest
from typer.testing import CliRunner
from todo_bene.infrastructure.cli.main import app
from todo_bene.infrastructure.config import save_user_config

runner = CliRunner()

try:
    # nécessaire avec le chiffrement de la base et la création systématique de la clé pendant les tests
    os.remove("test.db")
except FileNotFoundError:
    pass


@pytest.fixture
def test_config_env(tmp_path, monkeypatch):
    """Prépare un environnement de test avec une DB et une config isolées."""
    config_path = tmp_path / ".todo_bene.json"
    db_path = tmp_path / "test.db"

    monkeypatch.setenv("TODO_BENE_CONFIG_PATH", str(config_path))
    monkeypatch.setenv("TODO_BENE_DB_PATH", str(db_path))

    return config_path


def test_cli_priority_creation_and_display(test_config_env):
    """Test de la création d'un Todo prioritaire et de son étiquette."""
    user_id = "550e8400-e29b-41d4-a716-446655440000"
    save_user_config(user_id, "test.db", "test_profile")

    # Création avec le flag priority
    result = runner.invoke(
        app,
        ["add", "Urgent !", "--priority"],
        env={"TODO_BENE_CONFIG_PATH": str(test_config_env)},
    )
    assert result.exit_code == 0
    assert "prioritaire" in result.stdout  # .lower()

    # Vérification de l'étoile dans la liste
    result_list = runner.invoke(
        app, ["list", "--period", "all"], env={"TODO_BENE_CONFIG_PATH": str(test_config_env)}
    )
    assert "🔥" in result_list.stdout
    assert "Urgent !" in result_list.stdout


def test_cli_create_with_french_dates(test_config_env):
    """Vérifie que la CLI accepte et affiche correctement le format français JJ/MM/AAAA."""
    user_id = "550e8400-e29b-41d4-a716-446655440000"
    save_user_config(user_id, "test.db", "test_profile")
    start = pendulum.now().add(days=30)
    due = pendulum.now().add(days=45)
    # Utilisation du format FR à la création
    start_str = start.format("DD/MM/YYYY")
    due_str = due.format("DD/MM/YYYY")
    result = runner.invoke(
        app,
        ["add", "Réserver vacances", "--start", start_str, "--due", due_str],
        env={"TODO_BENE_CONFIG_PATH": str(test_config_env)},
    )
    assert result.exit_code == 0
    assert "Succès" in result.stdout

    # Vérification de l'affichage localisé dans la liste
    start_str = start.format("DD/MM")
    due_str = due.format("DD/MM")
    result_list = runner.invoke(
        app, ["list", "--period", "all"], env={"TODO_BENE_CONFIG_PATH": str(test_config_env)}
    )

    assert start_str + " 00:00" in result_list.stdout
    assert due_str + " 23:59" in result_list.stdout


def test_cli_default_date_logic(test_config_env, time_machine):
    """
    Vérifie les règles métier :
    1. Pas de start -> Heure actuelle de création.
    2. Pas de due -> Journée de start se terminant à 23:59.
    """
    user_id = "550e8400-e29b-41d4-a716-446655440000"
    save_user_config(user_id, "test.db", "test_profile")

    # On fige le temps au 11 Janvier 2026 à 15h30
    now_fixed = "2026-01-11 15:30:00"
    time_machine.move_to(now_fixed)

    # Act : Création sans aucune option de date
    runner.invoke(
        app,
        ["add", "Tâche auto-datée"],
        env={"TODO_BENE_CONFIG_PATH": str(test_config_env)},
    )

    # Assert : Vérification dans la liste au format FR
    result_list = runner.invoke(
        app, ["list", "--period", "all"], env={"TODO_BENE_CONFIG_PATH": str(test_config_env)}
    )

    # Doit afficher l'heure précise de création
    assert "11/01 15:30" in result_list.stdout
    # L'échéance par défaut doit être la fin de ce jour
    assert "11/01 23:59" in result_list.stdout


def test_cli_precise_hour_parsing_fr(test_config_env):
    """Vérifie le parsing d'une date française avec heure précise."""
    user_id = "550e8400-e29b-41d4-a716-446655440000"
    save_user_config(user_id, "test.db", "test_profile")

    with pendulum.travel_to("2026/02/12", freeze=True):

        runner.invoke(
            app,
            ["add", "Rendez-vous dentiste", "--start", "12/02/2026 14:15"],
            env={"TODO_BENE_CONFIG_PATH": str(test_config_env)},
        )

        result_list = runner.invoke(
            app, ["list", "--period", "all"], env={"TODO_BENE_CONFIG_PATH": str(test_config_env)}
        )
        assert "12/02 14:15" in result_list.stdout
        # L'échéance doit suivre sur le même jour à 23:59
        assert "12/02 23:59" in result_list.stdout


def test_cli_create_with_various_separators(test_config_env):
    """Vérifie que la CLI accepte les slashs ET les tirets pour le format FR."""
    user_id = "550e8400-e29b-41d4-a716-446655440000"
    save_user_config(user_id, "test.db", "test_profile")
    # Dates futures relatives
    pendulum.travel(freeze=True)
    date_tiret = pendulum.now().format("DD-MM-YYYY HH:mm")
    date_slash = pendulum.now().add(days=1).format("DD/MM/YYYY HH:mm")
    expected_slash1 = pendulum.now().format("DD/MM HH:mm")
    expected_slash2 = pendulum.now().add(days=1).format("DD/MM HH:mm")
    # Test avec tirets (ton cas d'erreur)
    runner.invoke(
        app,
        ["add", "Tiret test", "--start", date_tiret],
        env={"TODO_BENE_CONFIG_PATH": str(test_config_env)},
    )

    # Test avec slashs
    runner.invoke(
        app,
        ["add", "Slash test", "--start", date_slash],
        env={"TODO_BENE_CONFIG_PATH": str(test_config_env)},
    )
    pendulum.travel_back()
    result_list = runner.invoke(
        app, ["list", "--period", "all"], env={"TODO_BENE_CONFIG_PATH": str(test_config_env)}
    )
    assert expected_slash1 in result_list.stdout
    assert expected_slash2 in result_list.stdout


def test_cli_list_filter_by_category(test_config_env):
    """
    Vérifie que la commande 'list --category' filtre correctement les résultats.
    """
    user_id = "550e8400-e29b-41d4-a716-446655440000"
    save_user_config(user_id, "test.db", "test_profile")

    # 1. Création de deux tâches dans des catégories différentes
    runner.invoke(
        app,
        ["add", "Tâche Travail", "--category", "Travail"],
        env={"TODO_BENE_CONFIG_PATH": str(test_config_env)},
    )
    runner.invoke(
        app,
        ["add", "Tâche Maison", "--category", "Quotidien"],
        env={"TODO_BENE_CONFIG_PATH": str(test_config_env)},
    )

    # 2. Test du filtre : On ne veut voir que "Pro"
    result = runner.invoke(
        app,
        ["list", "--category", "Travail"],
        env={"TODO_BENE_CONFIG_PATH": str(test_config_env)},
    )
    # Assertions
    assert result.exit_code == 0
    assert "Tâche Travail" in result.stdout
    assert "Tâche Maison" not in result.stdout
