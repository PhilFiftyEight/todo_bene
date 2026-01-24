from dataclasses import FrozenInstanceError

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


# La catégorie ne peut-être modifiée
def test_category_not_mutable():
    category = Category(name="Quotidien")
    with pytest.raises(FrozenInstanceError):
        category.name = "Travail"


def test_category_creation_custom():
    # Une catégorie personnalisée est juste un nom nom modifiable
    cat = Category(name="Jardinage")
    assert cat.name == "Jardinage"
    with pytest.raises(FrozenInstanceError):
        cat.name = "Travail"

def test_category_validation_rules():
    # On pourrait décider qu'une catégorie ne peut pas être vide, sécurité
    with pytest.raises(ValueError, match="Le nom ne peut pas être vide"):
        Category(name="")