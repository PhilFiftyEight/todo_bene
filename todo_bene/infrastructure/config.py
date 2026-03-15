import os
import json
import sys
import re
import time
import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Any, Dict, Tuple, Optional, List
from uuid import UUID
import pendulum
import keyring
from cryptography.fernet import Fernet


class SensitiveDataFilter(logging.Filter):
    """Filtre de sécurité pour masquer les données sensibles dans les logs."""
    def filter(self, record):
        msg = str(record.msg)
        # 1. Masque la clé DuckDB (Hex 64 chars)
        msg = re.sub(r'[a-fA-F0-9]{64}', '***ENCRYPTED_KEY***', msg)
        # 2. Masque les emails (inclut _, -, ., +)
        # Le tiret '-' est placé à la fin pour ne pas créer d'intervalle invalide
        email_pattern = r'[a-zA-Z0-9._+\-]+@[a-zA-Z0-9._\-]+\.[a-zA-Z]{2,}'
        msg = re.sub(email_pattern, '***@email.com', msg)

        record.msg = msg
        return True


def setup_logging():
    """Initialise le logging sécurisé, localisé et avec rotation temporelle."""

    # Détection du mode test
    is_test = "pytest" in sys.modules or (len(sys.argv) > 0 and "pytest" in sys.argv[0])

    if is_test:
        # En test : on reste à la racine, on écrase à chaque run
        log_path = "todo_bene_test.log"
        handler = logging.FileHandler(log_path, mode='w', encoding='utf-8')
        level = logging.DEBUG
    else:
        # En prod : on utilise tes chemins standardisés
        # Puisque get_base_paths est dans le même fichier, on l'appelle directement
        _, data_dir = get_base_paths()
        log_dir = data_dir / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / "todo_bene.log"

        # Rotation hebdomadaire (le lundi), garde 4 archives (~1 mois)
        handler = TimedRotatingFileHandler(
            log_path,
            when='W0',
            backupCount=4,
            encoding='utf-8'
        )
        level = logging.INFO

    # Forcer l'utilisation de l'heure locale
    logging.Formatter.converter = time.localtime

    # Configuration de base
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(module)s - %(funcName)s - %(levelname)s - %(message)s',
        handlers=[handler]
    )

    # Injection du filtre
    root_logger = logging.getLogger()

    if not any(isinstance(f, SensitiveDataFilter) for f in root_logger.filters):
        root_logger.addFilter(SensitiveDataFilter())


# Variable globale pour le cache de session (mémoire vive uniquement)
_SESSION_MASTER_KEY = None

#     return stored_key.encode('utf-8')
def get_or_create_master_key() -> bytes:
    """
    Gère la clé maître avec cache de session.
    Stricte en prod, permissive uniquement en environnement de test.
    """
    global _SESSION_MASTER_KEY

    if _SESSION_MASTER_KEY is not None:
        return _SESSION_MASTER_KEY

    # Détection de l'environnement de test (via ta variable d'env existante)
    is_test = os.getenv("TODO_BENE_CONFIG_PATH") is not None and "pytest" in os.getenv("TODO_BENE_CONFIG_PATH", "")

    service_name = "todo_bene"
    key_alias = "master_key"

    try:
        stored_key = keyring.get_password(service_name, key_alias)
    except Exception as e:
        if not is_test:
            raise RuntimeError(f"Erreur fatale : Accès au trousseau système impossible : {e}")
        stored_key = None

    if stored_key:
        _SESSION_MASTER_KEY = stored_key.encode('utf-8')
    else:
        # Cas où la clé n'existe pas encore
        if is_test:
            # En test : on génère une clé volatile sans bloquer
            _SESSION_MASTER_KEY = Fernet.generate_key()
        else:
            # En prod : on crée la clé ET on exige le succès du stockage
            new_key = Fernet.generate_key().decode('utf-8')
            try:
                keyring.set_password(service_name, key_alias, new_key)
                _SESSION_MASTER_KEY = new_key.encode('utf-8')
            except Exception as e:
                raise RuntimeError(f"Impossible de stocker la clé de sécurité dans le système : {e}")

    return _SESSION_MASTER_KEY


def decrypt_value(encrypted_value: str) -> str:
    """
    Déchiffre une valeur (email, mot de passe) en utilisant la Master Key.
    Retourne la valeur en clair (string).
    """
    if not encrypted_value:
        return ""

    master_key = get_or_create_master_key()
    f = Fernet(master_key)

    try:
        # Fernet attend des bytes, on décode la chaîne chiffrée
        decrypted_bytes = f.decrypt(encrypted_value.encode('utf-8'))
        return decrypted_bytes.decode('utf-8')
    except Exception:
        # En cas d'erreur (mauvaise clé, donnée corrompue), on reste prudent
        return ""


def encrypt_value(plain_text: str) -> str:
    """
    Chiffre une valeur en utilisant la Master Key.
    Retourne la version chiffrée (string) prête à être stockée.
    """
    if not plain_text:
        return ""

    master_key = get_or_create_master_key()
    f = Fernet(master_key)

    # Fernet travaille sur des bytes, on encode le texte
    encrypted_bytes = f.encrypt(plain_text.encode('utf-8'))
    return encrypted_bytes.decode('utf-8')


def save_smtp_config(host: str, port: int, user: str, password: str):
    """
    Chiffre et sauvegarde les paramètres SMTP pour le profil actif.
    """
    user_id, db_path, profile_name = load_user_info()
    if not profile_name:
        return

    config = load_full_config()

    # Préparation des données chiffrées
    smtp_data = {
        "host": host,
        "port": port,
        "user_encrypted": encrypt_value(user),
        "password_encrypted": encrypt_value(password)
    }

    # Injection dans le profil
    if "profiles" in config and profile_name in config["profiles"]:
        config["profiles"][profile_name]["smtp_config"] = smtp_data
        save_full_config(config)


def add_mail_job(name: str, recipient: str, transformers: List[str], business_days_only: bool = False,
                 include_categories: list[str] = None,
                 exclude_categories: list[str] = None):
    """Ajoute un job de mail au profil actif."""
    user_id, db_path, profile_name = load_user_info()
    if not profile_name:
        return

    config = load_full_config()

    job_data = {
        "recipient": encrypt_value(recipient),
        "transformers": transformers,
        "business_days_only": business_days_only,
        "include_categories": include_categories or [],
        "exclude_categories": exclude_categories or []
    }

    # Initialisation de la section mail_jobs si elle n'existe pas
    profile = config["profiles"][profile_name]
    if "mail_jobs" not in profile:
        profile["mail_jobs"] = {}

    profile["mail_jobs"][name] = job_data
    save_full_config(config)


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
        "last_auto_postpone": "1970-01-01",
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
        config["profiles"][profile_name]["last_auto_postpone"] = (
            pendulum.now().to_date_string()
        )
        config_path, _ = get_base_paths()
        config_path.write_text(json.dumps(config, indent=4))

