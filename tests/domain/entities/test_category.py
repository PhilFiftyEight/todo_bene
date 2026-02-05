import pytest  # noqa: F401

from todo_bene.domain.entities.category import Category


# Test que les catégories de base existent
def test_base_categories_exist():
    assert Category.QUOTIDIEN == "Quotidien"
    assert Category.TRAVAIL == "Travail"
    assert Category.LOISIRS == "Loisirs"
    assert Category.SPORT == "Sport"
    assert Category.MEDICAL == "Médical"
    assert Category.FAMILLE == "Famille"


def test_category_creation_custom(user_id):
    cat = Category(name=" jardinage", user_id=user_id)
    assert cat.name == "Jardinage"  # clean name : strip, lower, capitalise


def test_category_validation_rules(user_id):
    # On pourrait décider qu'une catégorie ne peut pas être vide, sécurité
    with pytest.raises(ValueError, match="Le nom ne peut pas être vide"):
        Category(name="", user_id=user_id)
