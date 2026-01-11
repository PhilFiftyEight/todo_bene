from uuid import UUID
from todo_bene.domain.entities.todo import Todo
from todo_bene.application.interfaces.todo_repository import TodoRepository

class MemoryTodoRepository(TodoRepository):
    def __init__(self):
        self.todos = {}

    def save(self, todo: Todo) -> None:
        self.todos[todo.uuid] = todo

    def get_by_id(self, todo_id):
        return self.todos.get(todo_id)

    def find_by_parent(self, parent_id: UUID) -> list[Todo]:
        return [todo for todo in self.todos.values() if todo.parent == parent_id]

    def find_top_level_by_user(self, user_id: UUID) -> list[Todo]:
        return [
            todo for todo in self.todos.values() 
            if todo.user == user_id and todo.parent is None
        ]
