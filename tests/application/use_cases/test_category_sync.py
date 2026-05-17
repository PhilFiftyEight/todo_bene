import pytest
from uuid import uuid4
from todo_bene.application.use_cases.category_create import CategoryCreateUseCase
from todo_bene.infrastructure.persistence.duckdb.duckdb_category_repository import DuckDBCategoryRepository
from todo_bene.infrastructure.config import save_cached_categories, get_cached_categories, load_full_config, save_user_config

def test_category_creation_updates_db_and_cache(category_repo, repository, setup_test_env, user_id):
    """
    Vérifie que la création d'une catégorie met à jour la BDD ET le cache JSON.
    Note : Ce test échouera jusqu'à ce que la logique de cache soit intégrée.
    """
    
    # Création via le UseCase (simulation de l'action utilisateur)
    save_user_config(user_id, "test.db", "test_profile") # Ajout du profil
    use_case = CategoryCreateUseCase(category_repo)
    new_cat_name = "Jardinage"
    use_case.execute(new_cat_name, user_id)
    
    # 1. Vérification BDD
    assert category_repo.category_exists(new_cat_name, user_id) is True
    
    # 2. Vérification Cache JSON
    cached = get_cached_categories()
    if new_cat_name not in cached:
        print(f"\nDebug: cached={cached}")
        print(f"Debug: config={load_full_config()}")
    assert new_cat_name in cached
    
    # Vérification que le cache est bien dans le fichier config
    config = load_full_config()
    # On accède au profil actif pour vérifier la persistance
    active_profile = config.get("active_profile")
    profile_data = config.get("profiles", {}).get(active_profile, {})
    assert "cached_categories" in profile_data
    assert new_cat_name in profile_data["cached_categories"]
