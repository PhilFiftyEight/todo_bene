from uuid import UUID
from todo_bene.application.interfaces.todo_repository import TodoRepository


class TodoCompleteUseCase:
    def __init__(self, repository: TodoRepository):
        self.repository = repository

    def execute(self, todo_id: UUID, user_id: UUID, force: bool = False):
        # 1. Récupération et sécurité
        todo = self.repository.get_by_id(todo_id)
        if not todo or todo.user != user_id:
            return None

        # 2. BLOQUEUR : Vérifier s'il reste des enfants non terminés
        children = self.repository.find_by_parent(todo_id)
        active_children = [c for c in children if not c.state]

        # Si on ne force pas et qu'il y a des enfants actifs -> Erreur
        if active_children and not force:
            return {
                "success": False,
                "reason": "active_children",
                "active_count": len(active_children),
                "active_titles": [c.title for c in active_children],
            }
        # Si on force, on termine récursivement tous les descendants
        if force:
            self._complete_descendants(todo_id)

        # 3. On termine la tâche actuelle : Action de complétude
        self.repository.update_state(todo_id, True)

        # 4. Logique de remontée (inchangée)
        newly_pending_ids = self._get_newly_pending_parents(todo)

        return {
            "success": True,
            "completed_id": todo_id,
            "newly_pending_ids": newly_pending_ids,
            "is_root": todo.parent is None,
        }

    def _complete_descendants(self, parent_id: UUID):
        children = self.repository.find_by_parent(parent_id)
        for child in children:
            if not child.state:
                self._complete_descendants(child.uuid)
                self.repository.update_state(child.uuid, True)

    def _get_newly_pending_parents(self, todo):
        newly_pending_ids = []
        current_parent_id = todo.parent
        while current_parent_id is not None:
            siblings = self.repository.find_by_parent(current_parent_id)
            if all(s.state for s in siblings):
                newly_pending_ids.append(current_parent_id)
                p_obj = self.repository.get_by_id(current_parent_id)
                current_parent_id = p_obj.parent if p_obj else None
            else:
                break
        return newly_pending_ids
