from typing import List, Optional
from todo_bene.domain.entities.todo import Todo

class RepetitionTodo:
    def __init__(self, todo_repository):
        self.todo_repository = todo_repository

    def execute(self, todo_id: str) -> List[Todo] | None:
        original_todo = self.todo_repository.get_by_id(todo_id)
        
        # safeguard use case (Rule 1)
        if not original_todo or not original_todo.state or original_todo.parent:
            return None

        # Validate frequency
        if not original_todo.frequency:
            raise ValueError(f"Cannot repeat todo {todo_id} without a frequency set.")
            
        created_todos: List[Todo] = []
        
        # 2. Clone the root
        new_root = self._create_clone(original_todo)
        self.todo_repository.save(new_root)
        created_todos.append(new_root)
                
        # 3. Start recursion for descendants
        self._clone_children_recursive(original_todo.uuid, new_root.uuid, created_todos)
        
        return created_todos

    def _create_clone(self, source: Todo, new_parent_id: Optional[str] = None) -> Todo:
        return Todo(
            title=source.title,
            user=source.user,
            category=source.category,
            description=source.description,
            frequency=source.frequency if not new_parent_id else None,
            priority=source.priority,
            parent=new_parent_id
        )

    def _clone_children_recursive(self, old_parent_id: str, new_parent_id: str, created_list: List[Todo]):
        """Recursively find and clone all descendants."""
        children = self.todo_repository.find_by_parent(old_parent_id)
        for child in children:
            # Clone the child and link it to the NEW parent
            new_child = self._create_clone(child, new_parent_id=new_parent_id)
            self.todo_repository.save(new_child)
            created_list.append(new_child)
            
            # RECURSION: Look for this child's own children
            self._clone_children_recursive(child.uuid, new_child.uuid, created_list)
