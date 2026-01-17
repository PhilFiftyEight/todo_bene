from uuid import UUID
from todo_bene.application.interfaces.todo_repository import TodoRepository

    
class GetPendingCompletionParentsUseCase:
    def __init__(self, repository: TodoRepository):
        self.repository = repository

    def execute(self, user_id: UUID) -> list:
        return self.repository.get_pending_completion_parents(user_id)
