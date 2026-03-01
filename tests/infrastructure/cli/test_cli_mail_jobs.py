import pytest
from typer.testing import CliRunner
from todo_bene.infrastructure.cli.main import app
from todo_bene.infrastructure.config import load_full_config, decrypt_value, save_user_config
from uuid import uuid4

runner = CliRunner()

def test_add_mail_job_flow_with_questionary(tmp_path, monkeypatch, mocker):
    """Vérifie le flux CLI avec mocks Questionary (Password, Checkbox, Confirm)."""
    config_file = tmp_path / "config.json"
    monkeypatch.setenv("TODO_BENE_CONFIG_PATH", str(config_file))
    save_user_config(uuid4(), "test.db", "default")

    # Mock des Passwords (Email + Confirmation)
    mock_password = mocker.patch("questionary.password")
    # .side_effect permet de donner des réponses successives
    mock_password.return_value.ask.side_effect = ["boss@test.com", "boss@test.com"]

    # Mock de la Checkbox
    mock_checkbox = mocker.patch("questionary.checkbox")
    mock_checkbox.return_value.ask.return_value = ["format_phone"]

    # Mock du Confirm
    mock_confirm = mocker.patch("questionary.confirm")
    mock_confirm.return_value.ask.return_value = True

    # Action (On ne passe plus l'email dans input, seulement le Nom)
    inputs = "Rapport\n" 
    result = runner.invoke(app, ["mail", "add-job"], input=inputs)

    assert result.exit_code == 0
    config = load_full_config()
    assert "Rapport" in config["profiles"]["default"]["mail_jobs"]


def test_add_mail_job_flow_with_business_days(tmp_path, monkeypatch, mocker):
    """Vérifie que la CLI demande et enregistre l'option jours ouvrés."""
    # Setup
    config_file = tmp_path / "config.json"
    monkeypatch.setenv("TODO_BENE_CONFIG_PATH", str(config_file))

    save_user_config(uuid4(), "test.db", "default")

    # Mocks Questionary (Ordre d'exécution dans la CLI)
    
    # Mock des deux saisies Password (Email + Confirmation)
    mock_password = mocker.patch("questionary.password")
    mock_password.return_value.ask.side_effect = ["boss@test.com", "boss@test.com"]

    # Mock de la Checkbox
    mock_checkbox = mocker.patch("questionary.checkbox")
    mock_checkbox.return_value.ask.return_value = ["format_phone"]

    # Mock du Confirm pour Business Days
    mock_confirm = mocker.patch("questionary.confirm")
    mock_confirm.return_value.ask.return_value = True 

    # Action
    # Seul le nom du job reste dans le stdin de Typer
    inputs = "Job_Business\n"
    result = runner.invoke(app, ["mail", "add-job"], input=inputs)

    # Assertions
    assert result.exit_code == 0
    config = load_full_config()
    
    # Vérification de la présence de la clé et de la valeur
    assert "mail_jobs" in config["profiles"]["default"]
    job = config["profiles"]["default"]["mail_jobs"]["Job_Business"]
    assert job["business_days_only"] is True
