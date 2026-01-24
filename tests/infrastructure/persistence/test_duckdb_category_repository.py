import pytest  # noqa: F401
from uuid import uuid4
from todo_bene.domain.entities.category import Category

def test_duckdb_category_save_and_exists(category_repo, user_id):
    # GIVEN
    category = Category(name="Jardinage", user_id=user_id)
    
    # WHEN
    category_repo.save_category(category)
    
    # THEN
    assert category_repo.category_exists("Jardinage", user_id) is True
    assert category_repo.category_exists("jardinage", user_id) is True  # Casse
    assert category_repo.category_exists(" jardinage ", user_id) is True # Espaces

def test_duckdb_category_exists_is_user_specific(category_repo):
    # GIVEN
    user1 = uuid4()
    user2 = uuid4()
    category_repo.save_category(Category(name="Sport", user_id=user1))
    
    # THEN
    assert category_repo.category_exists("Sport", user1) is True
    assert category_repo.category_exists("Sport", user2) is False

def test_duckdb_get_all_categories(category_repo, user_id):
    # GIVEN
    categories = ["Zebra", "Alpha", "Beta"]
    for cat_name in categories:
        category_repo.save_category(Category(name=cat_name, user_id=user_id))
    
    # WHEN
    result = category_repo.get_all_categories(user_id)
    
    # THEN
    assert len(result) == 3
    # On vérifie le tri alphabétique (si tu l'as mis dans le SQL ORDER BY)
    assert result == ["Alpha", "Beta", "Zebra"]