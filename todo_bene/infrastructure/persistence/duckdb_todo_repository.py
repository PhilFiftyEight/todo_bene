from typing import Optional
import duckdb
from uuid import UUID
from todo_bene.domain.entities.todo import Todo

class DuckDBTodoRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path
        with duckdb.connect(self.db_path) as conn:
            # Création de la table avec toutes les colonnes de l'entité
            conn.execute("""
                CREATE TABLE IF NOT EXISTS todos (
                    uuid UUID PRIMARY KEY,
                    title TEXT,
                    user_id UUID,
                    category TEXT,
                    description TEXT,
                    parent_id UUID,
                    priority BOOLEAN DEFAULT FALSE,
                    date_start INTEGER,
                    date_due INTEGER,
                    date_final INTEGER DEFAULT 0
                )
            """)
            
            # Migration automatique pour ajouter les colonnes manquantes
            cols = conn.execute("PRAGMA table_info('todos')").fetchall()
            existing_cols = [c[1] for c in cols]
            
            migrations = {
                "priority": "BOOLEAN DEFAULT FALSE",
                "date_start": "INTEGER",
                "date_due": "INTEGER",
                "date_final": "INTEGER DEFAULT 0"
            }
            
            for col, definition in migrations.items():
                if col not in existing_cols:
                    conn.execute(f"ALTER TABLE todos ADD COLUMN {col} {definition}")

    def save(self, todo: Todo) -> None:
        with duckdb.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO todos 
                (uuid, title, user_id, category, description, parent_id, priority, date_start, date_due, date_final)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                todo.uuid, todo.title, todo.user, todo.category, 
                todo.description, todo.parent, todo.priority,
                todo.date_start, todo.date_due, todo.date_final
            ))


    def get_all_roots_by_user(self, user_id: UUID) -> list[Todo]:
        with duckdb.connect(self.db_path) as conn:
            results = conn.execute("""
                SELECT uuid, title, user_id, category, description, parent_id, priority, date_start, date_due, date_final
                FROM todos 
                WHERE user_id = ? AND parent_id IS NULL
            """, (user_id,)).fetchall()
            
            return [
                Todo(
                    uuid=row[0], title=row[1], user=row[2],
                    category=row[3], description=row[4],
                    parent=row[5], priority=row[6],
                    date_start=row[7], date_due=row[8], date_final=row[9]
                ) for row in results
            ]

    def get_all_by_user(self, user_id: UUID) -> list[Todo]:
        return self.get_all_roots_by_user(user_id)
    

    def get_by_id(self, todo_id: UUID) -> Optional[Todo]:
        with duckdb.connect(self.db_path) as conn:
            row = conn.execute("""
                SELECT uuid, title, user_id, category, description, parent_id, priority, date_start, date_due, date_final
                FROM todos WHERE uuid = ?
            """, (str(todo_id),)).fetchone()
            
            if not row:
                return None
            
            # Fonction utilitaire locale pour éviter de recréer un UUID si c'en est déjà un
            def to_uuid(val):
                if val is None: 
                    return None
                return val if isinstance(val, UUID) else UUID(val)

            return Todo(
                uuid=to_uuid(row[0]), 
                title=row[1], 
                user=to_uuid(row[2]),
                category=row[3], 
                description=row[4],
                parent=to_uuid(row[5]),
                priority=row[6], 
                date_start=row[7], 
                date_due=row[8], 
                date_final=row[9]
            )