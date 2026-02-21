from uuid import UUID
from typing import List
from todo_bene.domain.entities.category import Category
from todo_bene.application.interfaces.category_repository import CategoryRepository


class DuckDBCategoryRepository(CategoryRepository):

    def __init__(self, connection):
        self._conn = connection

    def category_exists(self, name: str, user_id: UUID) -> bool:
        # On crée une instance temporaire pour bénéficier du formatage du domaine
        # Cela garantit que si on cherche " sport ", on cherchera "Sport" en base
        formatted_name = Category(name=name, user_id=user_id).name

        result = self._conn.execute(
            "SELECT COUNT(*) FROM categories WHERE name = ? AND user_id = ?",
            [formatted_name, user_id],
        ).fetchone()
        return result[0] > 0

    def get_all_categories(self, user_id: UUID) -> List[str]:
        rows = self._conn.execute(
            "SELECT name FROM categories WHERE user_id = ? ORDER BY name", [user_id]
        ).fetchall()
        return [row[0] for row in rows]

    def save_category(self, category: Category) -> None:
        # On inclut l'émoji calculé par le domaine lors de l'insertion
        self._conn.execute(
            "INSERT INTO categories (name, user_id, emoji) VALUES (?, ?, ?)",
            [category.name, category.user_id, category.emoji],
        )

    def get_all_categories_with_emojis(self, user_id: UUID) -> List[Category]:
        """Récupère les objets Category complets avec leurs émojis stockés."""
        rows = self._conn.execute(
            "SELECT name, emoji FROM categories WHERE user_id = ? ORDER BY name", 
            [user_id]
        ).fetchall()
        return [Category(name=row[0], user_id=user_id, emoji=row[1]) for row in rows]
