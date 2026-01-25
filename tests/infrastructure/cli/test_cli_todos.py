import pytest
from typer.testing import CliRunner
from todo_bene.infrastructure.cli.main import app
from todo_bene.infrastructure.config import save_user_config
import os

runner = CliRunner()


@pytest.fixture
def test_config_env(tmp_path, monkeypatch):
    """Prépare un environnement de test avec une DB et une config isolées."""
    config_path = tmp_path / ".todo_bene.json"
    db_path = tmp_path / "test_todo.db"

    monkeypatch.setenv("TODO_BENE_CONFIG_PATH", str(config_path))
    monkeypatch.setenv("TODO_BENE_DB_PATH", str(db_path))

    return config_path


def test_cli_register_success(test_config_env):
    """Test de l'enregistrement d'un utilisateur."""
    result = runner.invoke(
        app, ["register", "--name", "Alice", "--email", "alice@test.com"]
    )
    assert result.exit_code == 0
    assert "Bienvenue Alice" in result.stdout
    assert os.path.exists(test_config_env)


def test_cli_priority_creation_and_display(test_config_env):
    """Test de la création d'un Todo prioritaire et de son étiquette."""
    user_id = "550e8400-e29b-41d4-a716-446655440000"
    save_user_config(user_id)

    # Création avec le flag priority
    result = runner.invoke(app, ["add", "Urgent !", "--priority"])
    assert result.exit_code == 0
    assert "prioritaire" in result.stdout#.lower()

    # Vérification de l'étoile dans la liste
    result_list = runner.invoke(app, ["list"])
    assert "🔥" in result_list.stdout
    assert "Urgent !" in result_list.stdout


def test_cli_create_with_french_dates(test_config_env):
    """Vérifie que la CLI accepte et affiche correctement le format français JJ/MM/AAAA."""
    user_id = "550e8400-e29b-41d4-a716-446655440000"
    save_user_config(user_id)

    # Utilisation du format FR à la création
    result = runner.invoke(
        app,
        ["add", "Réserver vacances", "--start", "01/06/2025", "--due", "15/06/2025"],
    )
    assert result.exit_code == 0
    assert "Succès" in result.stdout

    # Vérification de l'affichage localisé dans la liste
    result_list = runner.invoke(app, ["list"])
    assert "01/06/2025 00:00" in result_list.stdout
    assert "15/06/2025 23:59" in result_list.stdout


def test_cli_default_date_logic(test_config_env, time_machine):
    """
    Vérifie les règles métier :
    1. Pas de start -> Heure actuelle de création.
    2. Pas de due -> Journée de start se terminant à 23:59.
    """
    user_id = "550e8400-e29b-41d4-a716-446655440000"
    save_user_config(user_id)

    # On fige le temps au 11 Janvier 2026 à 15h30
    now_fixed = "2026-01-11 15:30:00"
    time_machine.move_to(now_fixed)

    # Act : Création sans aucune option de date
    runner.invoke(app, ["add", "Tâche auto-datée"])

    # Assert : Vérification dans la liste au format FR
    result_list = runner.invoke(app, ["list"])

    # Doit afficher l'heure précise de création
    assert "11/01/2026 15:30" in result_list.stdout
    # L'échéance par défaut doit être la fin de ce jour
    assert "11/01/2026 23:59" in result_list.stdout


def test_cli_precise_hour_parsing_fr(test_config_env):
    """Vérifie le parsing d'une date française avec heure précise."""
    user_id = "550e8400-e29b-41d4-a716-446655440000"
    save_user_config(user_id)

    runner.invoke(app, ["add", "Rendez-vous dentiste", "--start", "12/02/2026 14:15"])
    result_list = runner.invoke(app, ["list"])
    assert "12/02/2026 14:15" in result_list.stdout
    # L'échéance doit suivre sur le même jour à 23:59
    assert "12/02/2026 23:59" in result_list.stdout


def test_cli_create_with_various_separators(test_config_env):
    """Vérifie que la CLI accepte les slashs ET les tirets pour le format FR."""
    user_id = "550e8400-e29b-41d4-a716-446655440000"
    save_user_config(user_id)

    # Test avec tirets (ton cas d'erreur)
    runner.invoke(app, ["add", "Tiret test", "--start", "11-01-2026 13:00"])

    # Test avec slashs
    runner.invoke(app, ["add", "Slash test", "--start", "12/01/2026 14:00"])

    result_list = runner.invoke(app, ["list"])
    assert "11/01/2026 13:00" in result_list.stdout
    assert "12/01/2026 14:00" in result_list.stdout
