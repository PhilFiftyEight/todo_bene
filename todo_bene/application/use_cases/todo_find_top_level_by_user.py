from uuid import UUID
import pendulum
from todo_bene.application.interfaces.todo_repository import TodoRepository
from todo_bene.domain.entities.todo import Todo
from todo_bene.infrastructure.config import get_last_postpone_date, update_last_postpone_date


# Import de la règle métier (on peut la mettre dans un fichier business_rules.py ou ici)
def apply_auto_postpone(repository, user_id):
    # Vérification du fichier local
    today = pendulum.now().to_date_string()
    if get_last_postpone_date() == today:
        # On a déjà fait le ménage aujourd'hui, on quitte immédiatement
        return 0
    
    now_ts = pendulum.now().timestamp()
    new_due_ts = pendulum.now().at(23, 59, 59).timestamp()
    
    # On récupère TOUT pour gérer la hiérarchie
    active_todos = repository.find_all_active_by_user(user_id)

    if not active_todos:
        update_last_postpone_date() # On marque comme fait même si vide
        return 0
    
    postponed_count = 0

    roots = [t for t in active_todos if t.parent is None]
    children_map = {}
    for t in active_todos:
        if t.parent:
            children_map.setdefault(t.parent, []).append(t)

    def process(todo):
        nonlocal postponed_count # Pour modifier la variable du scope parent
        # Si en retard et non fini -> Report
        if not todo.state and todo.date_due < now_ts:
            todo.date_due = new_due_ts
            repository.save(todo)
            postponed_count += 1
            
        # On descend dans les enfants
        for child in children_map.get(todo.uuid, []):
            process(child)

    for root in roots:
        process(root)
    
    # CLÔTURE : On enregistre le passage réussi
    update_last_postpone_date()
    return postponed_count

  
class TodoGetAllRootsByUserUseCase:
    def __init__(self, todo_repo: TodoRepository):
        self.todo_repo = todo_repo

    def execute(self, user_id: UUID, category: str = None) -> list[Todo]:
        # 1. Application de la règle métier système
        count = apply_auto_postpone(self.todo_repo, user_id)
        roots = self.todo_repo.find_top_level_by_user(user_id, category=category)
        return roots, count
