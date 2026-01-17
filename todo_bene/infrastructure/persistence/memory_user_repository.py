from todo_bene.domain.entities.user import User
from todo_bene.application.interfaces.user_repository import UserRepository


class MemoryUserRepository(UserRepository):
    def __init__(self):
        self.users = {}  # Notre dictionnaire est maintenant encapsulé ici

    def save(self, user: User) -> None:
        self.users[user.uuid] = user

    def get_by_id(self, user_id):  # On anticipe un peu le besoin
        return self.users.get(user_id)
