
from todo_bene.domain.entities.todo import Todo


class RepetitionTodo:
    def __init__(self, todo_repository):
        self.todo_repository = todo_repository

    def execute(self, todo_id):
        # 1. Récupération de l'original
        todo = self.todo_repository.get_by_id(todo_id)
        if not todo:
            return None

        # Étape 1 : Si la tâche n'est pas terminée, ou 
        # c'est une tâche enfant, on s'arrête là
        if not todo.state or todo.parent:
            return None
            
        created_todos = []
        
        # Cas 3 : On crée la répétition
        if todo.frequency:
            new_todo = Todo(
                title=todo.title,
                user=todo.user,
                category=todo.category,
                description=todo.description,
                frequency=todo.frequency,
                priority=todo.priority
                # date_start/due gérés par le domaine
            )
            self.todo_repository.save(new_todo)
            created_todos.append(new_todo)
        
        return created_todos if created_todos else None