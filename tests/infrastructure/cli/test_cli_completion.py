import pytest  # noqa: F401
from todo_bene.infrastructure.cli.main import complete_category
from todo_bene.domain.entities.category import Category

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
