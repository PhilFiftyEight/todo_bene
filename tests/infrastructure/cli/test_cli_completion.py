import pytest  # noqa: F401
from todo_bene.infrastructure.cli.main import complete_category
from todo_bene.domain.entities.category import Category
from todo_bene.application.use_cases.category_create import CategoryCreateUseCase 
from todo_bene.infrastructure.config import save_user_config

def test_complete_category_returns_all_on_empty():
    """Si l'utilisateur n'a rien tapé, on propose tout."""
    suggestions = complete_category("")
    # On vérifie qu'on retrouve bien nos catégories de base
    assert Category.QUOTIDIEN in suggestions
    assert len(suggestions) == len(Category.ALL)


def test_complete_category_filters_results():
    """Si l'utilisateur tape 'Tra', on ne veut que 'Travail'."""
    suggestions = complete_category("Tra")
    assert "Travail" in suggestions
    assert "Quotidien" not in suggestions


def test_complete_category_is_case_insensitive():
    """La complétion ne doit pas être sensible à la casse."""
    suggestions = complete_category("sport")
    assert "Sport" in suggestions


def test_complete_category_suggests_category_user_with_cache(user_id, category_repo):
    """Vérifie que pour une catégorie utilisateur est bien proposé"""
    save_user_config(user_id, "test.db", "test_profile") # Ajout du profil
    use_case = CategoryCreateUseCase(category_repo)
    new_cat_name = "Jardinage"
    use_case.execute(new_cat_name, user_id)
    suggestions = complete_category("Jar")
    assert "Jardinage" in suggestions
