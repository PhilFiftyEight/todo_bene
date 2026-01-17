from uuid import UUID
from todo_bene.application.interfaces.todo_repository import TodoRepository

class TodoCompleteUseCase:
    def __init__(self, repository: TodoRepository):
        self.repository = repository

    def execute(self, todo_id: UUID, user_id: UUID):
        # 1. On récupère la tâche
        todo = self.repository.get_by_id(todo_id)
        
        # 2. Si elle n'existe pas, on pourrait lever une erreur (optionnel pour le test actuel)
        if not todo:
            return 
            
        # 3. On demande au repository de mettre à jour l'état à True
        self.repository.update_state(todo_id, True)