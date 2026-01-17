from uuid import UUID
from todo_bene.application.interfaces.todo_repository import TodoRepository
from todo_bene.domain.entities.todo import Todo


class TodoGetAllRootsByUserUseCase:
    def __init__(self, todo_repo: TodoRepository):
        self.todo_repo = todo_repo

    def execute(self, user_id: UUID) -> list[Todo]:
        return self.todo_repo.find_top_level_by_user(user_id)
