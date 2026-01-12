import duckdb
from uuid import UUID
from typing import Optional, List
from todo_bene.domain.entities.todo import Todo

class DuckDBTodoRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ensure_table_exists()

    def _ensure_table_exists(self):
        with duckdb.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS todos (
                    uuid UUID PRIMARY KEY,
                    title TEXT NOT NULL,
                    user_id UUID NOT NULL,
                    category TEXT,
                    description TEXT,
                    parent_id UUID,
                    priority BOOLEAN DEFAULT FALSE,
                    frequency TEXT,
                    state BOOLEAN DEFAULT FALSE,
                    date_start INTEGER,
                    date_due INTEGER,
                    date_final INTEGER DEFAULT 0
                )
            """)

    def _map_row_to_todo(self, row) -> Todo:
        """Transforme une ligne SQL en objet Todo."""
        if not row: 
            return None
        return Todo(
            uuid=row[0] if isinstance(row[0], UUID) else UUID(row[0]),
            title=row[1],
            user=row[2] if isinstance(row[2], UUID) else UUID(row[2]),
            category=row[3],
            description=row[4],
            parent=(row[5] if isinstance(row[5], UUID) else UUID(row[5])) if row[5] else None,
            priority=row[6],
            frequency=row[7] if row[7] else "",
            state=row[8],
            date_start=row[9],
            date_due=row[10],
            date_final=row[11]
        )

    def save(self, todo: Todo):
        # Conversion du tuple frequency en string pour le stockage si nécessaire
        freq_str = f"{todo.frequency[0]},{todo.frequency[1]}" if isinstance(todo.frequency, tuple) else todo.frequency

        with duckdb.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO todos (
                    uuid, title, user_id, category, description, parent_id, 
                    priority, frequency, state, date_start, date_due, date_final
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(todo.uuid), todo.title, str(todo.user), todo.category, todo.description,
                str(todo.parent) if todo.parent else None,
                todo.priority, freq_str, todo.state, todo.date_start, todo.date_due, todo.date_final
            ))

    def get_by_id(self, todo_id: UUID) -> Optional[Todo]:
        with duckdb.connect(self.db_path) as conn:
            row = conn.execute("SELECT * FROM todos WHERE uuid = ?", (str(todo_id),)).fetchone()
            return self._map_row_to_todo(row)

    def get_all_roots_by_user(self, user_id: UUID) -> List[Todo]:
        with duckdb.connect(self.db_path) as conn:
            rows = conn.execute("SELECT * FROM todos WHERE user_id = ? AND parent_id IS NULL", (str(user_id),)).fetchall()
            return [self._map_row_to_todo(r) for r in rows]

    def get_children(self, parent_id: UUID) -> List[Todo]:
        with duckdb.connect(self.db_path) as conn:
            rows = conn.execute("SELECT * FROM todos WHERE parent_id = ?", (str(parent_id),)).fetchall()
            return [self._map_row_to_todo(r) for r in rows]
