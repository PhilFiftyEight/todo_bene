from todo_bene.domain.entities.user import User
from todo_bene.application.interfaces.user_repository import UserRepository


class UserCreateUseCase:
    def __init__(self, repo: UserRepository):
        # On injecte l'interface, pas le dictionnaire
        self.repo = repo

    def execute(self, name: str, email: str) -> User:
        user = User(name=name, email=email)

        # On utilise la méthode définie dans l'interface
        self.repo.save(user)

        return user
