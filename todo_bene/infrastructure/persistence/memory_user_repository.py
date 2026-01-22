from uuid import UUID
from todo_bene.domain.entities.user import User
from todo_bene.application.interfaces.user_repository import UserRepository


class MemoryUserRepository(UserRepository):  # Ou le nom exact dans ton fichier de test
    def __init__(self):
        self.users = {}

    def save_user(self, user: User):
        self.users[user.uuid] = user

    def get_user_by_email(self, email: str):
        return next((u for u in self.users.values() if u.email == email), None)

    def get_by_id(self, uuid: UUID):
        return self.users[uuid]
