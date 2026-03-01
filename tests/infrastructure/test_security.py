import pytest
from uuid import uuid4
from todo_bene.infrastructure.config import (
    encrypt_value,
    decrypt_value,
    save_user_config,
    save_smtp_config,
    load_full_config,
    add_mail_job
)

def test_security_roundtrip():
    """
    Vérifie que la chaîne de chiffrement/déchiffrement est intègre.
    Note : Ce test déclenchera un prompt macOS s'il n'est pas déjà autorisé.
    """
    original_secret = "mon_secret_smtp_2026"
    
    # Chiffrement
    token = encrypt_value(original_secret)
    assert token != original_secret
    assert isinstance(token, str)
    
    # Déchiffrement
    decrypted_result = decrypt_value(token)
    
    # Validation
    assert decrypted_result == original_secret
    print(f"\n[OK] Secret préservé : {decrypted_result}")

def test_decrypt_empty_or_invalid():
    """Vérifie la robustesse face aux données invalides."""
    assert decrypt_value("") == ""
    assert decrypt_value("mauvais_token_non_fernet") == ""

def test_save_and_load_smtp_config(tmp_path, monkeypatch):
    """Vérifie le cycle complet d'écriture et lecture du SMTP."""
    # Simulation d'un environnement de config temporaire
    config_file = tmp_path / "config.json"
    monkeypatch.setenv("TODO_BENE_CONFIG_PATH", str(config_file))
    
    u_id = uuid4()
    save_user_config(u_id, "fake.db", "test_profile")
    
    # Sauvegarde SMTP
    raw_user = "mon.email@test.com"
    raw_pass = "password123"
    save_smtp_config("smtp.test.com", 587, raw_user, raw_pass)
    
    # Vérifications
    full_config = load_full_config()
    smtp_cfg = full_config["profiles"]["test_profile"]["smtp_config"]
    
    # Vérifie que ce n'est pas stocké en clair
    assert smtp_cfg["user_encrypted"] != raw_user
    assert smtp_cfg["password_encrypted"] != raw_pass
    
    # Vérifie que c'est déchiffrable
    assert decrypt_value(smtp_cfg["user_encrypted"]) == raw_user
    assert decrypt_value(smtp_cfg["password_encrypted"]) == raw_pass


def test_add_mail_job_persistence(tmp_path, monkeypatch):
    """Vérifie qu'un job est correctement ajouté au profil."""
    # Setup
    config_file = tmp_path / "config.json"
    monkeypatch.setenv("TODO_BENE_CONFIG_PATH", str(config_file))
    save_user_config(uuid4(), "test.db", "profile_test")

    # Action
    job_name = "Rapport Pro"
    recipient = "boss@company.com"
    transformers = ["format_phone", "waze_link"]
    
    add_mail_job(job_name, recipient, transformers)

    # Assertions
    config = load_full_config()
    jobs = config["profiles"]["profile_test"]["mail_jobs"]
    
    assert job_name in jobs
    assert jobs[job_name]["recipient"] != recipient
    # Vérifie le déchiffrement
    assert decrypt_value(jobs[job_name]["recipient"]) == recipient
    assert jobs[job_name]["transformers"] == ["format_phone", "waze_link"]


def test_add_mail_job_business_days_persistence(tmp_path, monkeypatch):
    """Vérifie que l'option business_days_only est bien sauvegardée."""
    # Setup
    config_file = tmp_path / "config.json"
    monkeypatch.setenv("TODO_BENE_CONFIG_PATH", str(config_file))
    save_user_config(uuid4(), "test.db", "profile_test")

    # Action : Création d'un job avec l'option activée
    add_mail_job("Job Pro", "test@pro.com", [], business_days_only=True)

    # Assertions
    config = load_full_config()
    job = config["profiles"]["profile_test"]["mail_jobs"]["Job Pro"]
    
    assert job["business_days_only"] is True
