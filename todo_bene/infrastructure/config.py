import os
import json
from pathlib import Path
from typing import Any, Dict, Tuple, Optional
from uuid import UUID
import pendulum

def get_base_paths() -> Tuple[Path, Path]:
    """
    Définit les chemins pour la config et les données.
    Si TODO_BENE_CONFIG_PATH est défini, on utilise ce fichier et son dossier.
    """
    env_config_path = os.getenv("TODO_BENE_CONFIG_PATH")
    
    if env_config_path:
        config_file = Path(env_config_path)
        # En test, on met la DB dans le même dossier temporaire
        return config_file, config_file.parent

    # Chemins standards hors tests
    config_dir = Path.home() / ".config" / "todo_bene"
    data_dir = Path.home() / ".local" / "share" / "todo_bene"
    config_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "config.json", data_dir

def load_full_config() -> Dict[str, Any]:
    """Charge l'intégralité du fichier config.json."""
    config_path, _ = get_base_paths()
    if not config_path.exists():
        return {"profiles": {}, "active_profile": None}
    try:
        return json.loads(config_path.read_text())
    except (json.JSONDecodeError, OSError):
        return {"profiles": {}, "active_profile": None}

def save_full_config(config: Dict[str, Any]):
    """Sauvegarde le dictionnaire complet."""
    config_path, _ = get_base_paths()
    config_path.write_text(json.dumps(config, indent=4))

def load_user_info() -> Tuple[Optional[UUID], Optional[str], Optional[str]]:
    """Récupère les infos du profil actif (ID, DB, Nom)."""
    data = load_full_config()
    active_name = data.get("active_profile")
    if not active_name or active_name not in data.get("profiles", {}):
        return None, None, None
    
    profile = data["profiles"][active_name]
    try:
        u_id = UUID(profile["user_id"])
        return u_id, profile.get("db_path"), active_name
    except (ValueError, KeyError):
        return None, None, None

def save_user_config(user_id: UUID, db_path: str, profile_name: str):
    """Crée ou met à jour un profil et le définit comme actif."""
    config = load_full_config()
    if "profiles" not in config:
        config["profiles"] = {}
    
    config["profiles"][profile_name] = {
        "user_id": str(user_id),
        "db_path": db_path,
        "last_auto_postpone": "1970-01-01"
    }
    config["active_profile"] = profile_name
    save_full_config(config)

# # --- Gestion du report automatique par profil ---

def get_last_postpone_date() -> Optional[str]:
    _, _, profile_name = load_user_info()
    config = load_full_config()
    return config.get("profiles", {}).get(profile_name, {}).get("last_auto_postpone")

def update_last_postpone_date():
    user_id, db_path, profile_name = load_user_info()
    if not profile_name: 
        return
    
    config = load_full_config()
    if "profiles" in config and profile_name in config["profiles"]:
        config["profiles"][profile_name]["last_auto_postpone"] = pendulum.now().to_date_string()
        config_path, _ = get_base_paths()
        config_path.write_text(json.dumps(config, indent=4))

# def get_last_postpone_date() -> str:
#     """Récupère la date du dernier report automatique pour le profil actif."""
#     config = load_full_config()
#     active = config.get("active_profile")
#     if active and active in config.get("profiles", {}):
#         return config["profiles"][active].get("last_auto_postpone", "1970-01-01")
#     return "1970-01-01"

# def update_last_postpone_date(date_str: str):
#     """Met à jour la date du dernier report pour le profil actif."""
#     config = load_full_config()
#     active = config.get("active_profile")
#     if active and active in config.get("profiles", {}):
#         config["profiles"][active]["last_auto_postpone"] = date_str
#         save_full_config(config)