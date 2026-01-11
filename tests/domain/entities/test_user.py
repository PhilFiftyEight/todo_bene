import pytest  # noqa: F401
from uuid import UUID
from todo_bene.domain.entities.user import User


def test_user_creation():
    # Arrange & Act
    user = User(name="Jean Dupont", email="jean.dupont@example.com")

    # Assert
    assert user.name == "Jean Dupont"
    assert user.email == "jean.dupont@example.com"
    assert isinstance(user.uuid, UUID) # L'ID doit être généré automatiquement

