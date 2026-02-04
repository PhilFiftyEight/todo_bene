# from pathlib import Path
import pytest
from typer.testing import CliRunner
from todo_bene.infrastructure.cli.main import app

runner = CliRunner()
def test_auto_wizard_on_first_launch(tmp_path, monkeypatch):
    """
    Vérifie que le wizard s'active automatiquement si aucune config n'existe.
    """
    # GIVEN: Un environnement vierge (pas de config.json)
    config_dir = tmp_path / ".todo_bene"
    config_file = config_dir / "config.json"
    
    # On crée les répertoires physiques pour que l'app puisse écrire dedans
    config_dir.mkdir(parents=True, exist_ok=True)

    # On mocke partout où c'est importé pour être sûr
    paths = (config_dir, config_dir) # config et data au même endroit pour le test
    monkeypatch.setattr("todo_bene.infrastructure.cli.main.get_base_paths", lambda: paths)
    
    # On force la variable d'environnement que load_user_info utilise
    monkeypatch.setenv("TODO_BENE_CONFIG_PATH", str(config_file))
    
    # WHEN: On lance une commande lambda (ex: list)
    # Inputs: email, nom, is_dev (n), [entrée pour finir]
    inputs = "test@example.com\nPhilippe\nn\n"
    result = runner.invoke(app, ["list"], input=inputs)

    # THEN:
    # 1. On doit voir la bannière et les questions
    assert "Configurons votre profil pour commencer" in result.stdout
    assert "Veuillez saisir votre email" in result.stdout
    
    # 2. Le fichier config.json doit avoir été créé
    assert config_file.exists()
    
    # 3. La base de données doit être créée au bon endroit (mode prod par défaut ici)
    db_path = config_dir / ".todo_bene.db"
    assert db_path.exists()
    
    # 4. Le profil doit être correct dans le fichier
    import json
    config_data = json.loads(config_file.read_text())
    assert config_data["active_profile"] == "Philippe_prod"