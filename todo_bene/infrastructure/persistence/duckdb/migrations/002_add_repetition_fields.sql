-- Migration 002 : Ajout des champs pour la gestion de la répétition
-- frequency : stocke l'instruction DSL (ex: 'tomorrow', 'every monday')
-- date_final : stocke la date de fin réelle de la tâche

ALTER TABLE todos ADD COLUMN frequency VARCHAR DEFAULT '';
ALTER TABLE todos ADD COLUMN date_final DOUBLE;
