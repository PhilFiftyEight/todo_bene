from uuid import UUID
from todo_bene.application.interfaces.todo_repository import TodoRepository


class TodoDeleteUseCase:
    def __init__(self, repository: TodoRepository):
        self.repository = repository

    def execute(self, todo_id: UUID, user_id: UUID) -> None:
        """
        Exécute la suppression d'un Todo.
        Vérifie l'existence et la propriété avant de supprimer récursivement.
        """
        # 1. Récupération du Todo
        todo = self.repository.get_by_id(todo_id)

        # 2. Si le Todo n'existe pas, on ne fait rien (idempotence)
        if not todo:
            return

        # 3. Vérification de sécurité : l'utilisateur est-il le propriétaire ?
        if todo.user != user_id:
            raise ValueError("Vous n'avez pas l'autorisation de supprimer ce Todo.")

        # 4. Délégation de la suppression récursive au repository
        self.repository.delete(todo_id)
