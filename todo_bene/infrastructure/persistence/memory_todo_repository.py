from uuid import UUID
from todo_bene.domain.entities.todo import Todo
from todo_bene.application.interfaces.todo_repository import TodoRepository

class MemoryTodoRepository(TodoRepository):
    def __init__(self):
        self.todos = {}

    def save(self, todo: Todo) -> None:
        self.todos[todo.uuid] = todo

    def get_by_id(self, todo_id: UUID) -> Todo | None:
        return self.todos.get(todo_id)

    def find_by_parent(self, parent_id: UUID) -> list[Todo]:
        return [todo for todo in self.todos.values() if todo.parent == parent_id]

    def find_top_level_by_user(self, user_id: UUID) -> list[Todo]:
        return [
            todo for todo in self.todos.values() 
            if todo.user == user_id and todo.parent is None and not todo.state
        ]

    def search_by_title(self, user_id: UUID, search_term: str) -> list[Todo]:
        return [
            todo for todo in self.todos.values()
            if todo.user == user_id and search_term.lower() in todo.title.lower()
        ]

    def delete(self, todo_id: UUID) -> None:
        # On trouve tous les enfants d'abord
        children = self.find_by_parent(todo_id)
        for child in children:
            self.delete(child.uuid) # Appel récursif
        
        # On supprime le todo lui-même
        if todo_id in self.todos:
            del self.todos[todo_id]

    def update_state(self, todo_id: UUID, state: bool):
        if todo_id in self.todos:
            self.todos[todo_id].state = state

    def get_pending_completion_parents(self, user_id: UUID) -> list[Todo]:
            all_todos = self.todos.values()
            parents = [t for t in all_todos if t.user == user_id and not t.state]
            
            results = []
            for p in parents:
                children = [t for t in all_todos if t.parent == p.uuid]
                if children and all(c.state for c in children):
                    results.append(p)
            return results
    