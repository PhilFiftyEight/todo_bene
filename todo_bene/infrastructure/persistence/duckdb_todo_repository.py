import duckdb
from uuid import UUID
from typing import List, Optional
from todo_bene.domain.entities.todo import Todo

class DuckDBTodoRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path
        # On garde une connexion unique pour toute la durée de vie du repo
        self._conn = duckdb.connect(self.db_path)
        self._init_db()

    def _init_db(self):
        # Ici on n'utilise pas 'with' pour ne pas fermer self._conn
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS todos (
                uuid UUID PRIMARY KEY,
                title VARCHAR,
                description TEXT,
                category VARCHAR,
                state BOOLEAN,
                priority BOOLEAN,
                date_start DOUBLE,
                date_due DOUBLE,
                user_id UUID,
                parent_id UUID
            )
        """)

    def save(self, todo: Todo):
        self._conn.execute("""
            INSERT OR REPLACE INTO todos 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            todo.uuid, todo.title, todo.description, todo.category,
            todo.state, todo.priority, todo.date_start, todo.date_due,
            todo.user, todo.parent
        ))

    def get_by_id(self, todo_id: UUID) -> Optional[Todo]:
        res = self._conn.execute("SELECT * FROM todos WHERE uuid = ?", (todo_id,)).fetchone()
        if res:
            return self._row_to_todo(res)
        return None

    def get_all_roots_by_user(self, user_id: UUID) -> List[Todo]:
        query = """
            SELECT uuid, title, description, category, state, priority, date_start, date_due, user_id, parent_id 
            FROM todos 
            WHERE user_id = ? AND parent_id IS NULL 
            ORDER BY date_start ASC
        """
        rows = self._conn.execute(query, (user_id,)).fetchall()
        return [self._row_to_todo(row) for row in rows]

    def get_children(self, parent_id: UUID) -> List[Todo]:
        query = """
            SELECT uuid, title, description, category, state, priority, date_start, date_due, user_id, parent_id 
            FROM todos 
            WHERE parent_id = ? 
            ORDER BY date_start ASC
        """
        rows = self._conn.execute(query, (parent_id,)).fetchall()
        return [self._row_to_todo(row) for row in rows]

    def search_by_title(self, user_id: UUID, search_term: str) -> List[Todo]:
        query = """
            SELECT uuid, title, description, category, state, priority, 
                   date_start, date_due, user_id, parent_id 
            FROM todos 
            WHERE user_id = ? AND title ILIKE ?
            ORDER BY title ASC
            LIMIT 10
        """
        rows = self._conn.execute(query, (user_id, f"%{search_term}%")).fetchall()
        return [self._row_to_todo(row) for row in rows]

    def _row_to_todo(self, row) -> Todo:
        return Todo(
            uuid=row[0],
            title=row[1],
            description=row[2],
            category=row[3],
            state=row[4],
            priority=row[5],
            date_start=row[6],
            date_due=row[7],
            user=row[8],
            parent=row[9]
        )
    
    def __del__(self):
        """Ferme proprement la connexion quand l'objet est détruit."""
        try:
            self._conn.close()
        except:  # noqa: E722
            pass