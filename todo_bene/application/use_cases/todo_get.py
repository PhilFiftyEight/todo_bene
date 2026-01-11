from uuid import UUID
from todo_bene.domain.entities.todo import Todo
from todo_bene.application.interfaces.todo_repository import TodoRepository

class TodoGetUseCase:
    def __init__(self, todo_repo: TodoRepository):
        self.todo_repo = todo_repo

    def execute(self, todo_id: UUID, user_id: UUID) -> Todo | None:
        # On délègue simplement la récupération au repository
        todo = self.todo_repo.get_by_id(todo_id)
        # Vérification : existence ET propriété
        if not todo or todo.user != user_id:
            return None, []
            
        # On récupère les enfants associés à ce Todo
        children = self.todo_repo.find_by_parent(todo_id)        
        return todo, children 


# ajouter la règle: un utilisateur ne peut voir que ses propres Todos