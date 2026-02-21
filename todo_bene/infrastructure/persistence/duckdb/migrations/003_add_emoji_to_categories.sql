-- Ajout de la colonne emoji aux catégories personnalisées existantes
ALTER TABLE categories ADD COLUMN emoji TEXT DEFAULT '🏷️';
