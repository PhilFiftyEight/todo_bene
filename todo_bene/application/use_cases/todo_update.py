# todo_bene/application/use_cases/todo_update.py
from uuid import UUID

class TodoUpdateUseCase:
    def __init__(self, repository):
        self.repository = repository

    def execute(self, todo_id: UUID, **kwargs):
        todo = self.repository.get_by_id(todo_id)
        if not todo:
            raise ValueError("Todo non trouvé")

        # Règle : Si c'est un enfant, vérifications par rapport au parent
        if todo.parent:
            parent = self.repository.get_by_id(todo.parent)
            
            # Verrou de catégorie
            if 'category' in kwargs and kwargs['category'] != parent.category:
                raise ValueError("La catégorie d'un enfant est verrouillée sur celle du parent")
            
            # Verrou de date_due
            new_due = kwargs.get('date_due', todo.date_due)
            if new_due > parent.date_due:
                raise ValueError("L'échéance de l'enfant ne peut pas dépasser celle du parent")

        # 2. On délègue la validation génétique à l'entité
        forbiden = todo.update(**kwargs)
        
        # 3. Persistance
        self.repository.save(todo)
        
        return forbiden