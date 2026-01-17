import pytest  # noqa: F401
from todo_bene.application.use_cases.user_create import UserCreateUseCase
from todo_bene.infrastructure.persistence.memory_user_repository import (
    MemoryUserRepository,
)


def test_user_create_use_case():
    # Arrange
    repo = MemoryUserRepository()  # On utilise l'implémentation de test
    use_case = UserCreateUseCase(repo)

    name = "Jean Dupont"
    email = "jean.dupont@example.com"

    # Act
    user = use_case.execute(name, email)

    # Assert
    assert user.name == name
    # On vérifie via le repo
    assert repo.get_by_id(user.uuid) == user
