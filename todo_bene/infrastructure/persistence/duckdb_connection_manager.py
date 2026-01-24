import duckdb

class DuckDBConnectionManager:
    def __init__(self, db_path: str):
        self.conn = duckdb.connect(db_path)
        self._init_schema()

    def _init_schema(self):
        """Initialise le schéma global (Users, Todos, Categories)."""
        # Table Users
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                uuid UUID PRIMARY KEY,
                name TEXT,
                email TEXT UNIQUE
            )
        """)
        # Table Todos
        self.conn.execute("""
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
        # Table Categories
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                name TEXT,
                user_id UUID,
                PRIMARY KEY (name, user_id)
            )
        """)

    def get_connection(self):
        return self.conn

    def close(self):
        if self.conn:
            self.conn.close()
