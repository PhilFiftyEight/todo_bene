import pytest
from uuid import uuid4
from todo_bene.infrastructure.config import encrypt_value, decrypt_value, save_user_config, save_smtp_config, load_full_config

def test_security_roundtrip():
    """
    Vérifie que la chaîne de chiffrement/déchiffrement est intègre.
    Note : Ce test déclenchera un prompt macOS s'il n'est pas déjà autorisé.
    """
    original_secret = "mon_secret_smtp_2026"
    
    # 1. Chiffrement
    token = encrypt_value(original_secret)
    assert token != original_secret
    assert isinstance(token, str)
    
    # 2. Déchiffrement
    decrypted_result = decrypt_value(token)
    
    # 3. Validation
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
