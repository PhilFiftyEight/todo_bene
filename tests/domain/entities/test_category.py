from dataclasses import FrozenInstanceError

import pytest  # noqa: F401

from todo_bene.domain.entities.category import Category


def test_category_creation():
    category = Category(name="quotidien")
    assert category.name == "quotidien"


def test_category_not_mutable():
    category = Category(name="quotidien")
    with pytest.raises(FrozenInstanceError, match=r"cannot assign to field 'name'"):
        category.name = "mensuel"
