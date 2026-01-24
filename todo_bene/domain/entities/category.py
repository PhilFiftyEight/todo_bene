from dataclasses import dataclass
from uuid import UUID


@dataclass
class Category:
    name: str
    user_id: UUID

    # Constantes pour faciliter l'usage dans le code
    QUOTIDIEN = "Quotidien"
    TRAVAIL = "Travail"
    LOISIRS = "Loisirs"
    SPORT = "Sport"
    MEDICAL = "Médical"
    FAMILLE = "Famille"

    # Liste pour la validation et la future complétion Typer
    ALL = [QUOTIDIEN, TRAVAIL, LOISIRS, SPORT, MEDICAL, FAMILLE]

    def __post_init__(self):
        """ Règles de domaine : 
            - une catégorie doit avoir un nom non vide
            - name est sous la forme : "Essai"
            - formats corrigés : " Essai", "essai", "ESSAI", "Essai "
        """
        self.name = self.name.strip()
        if not self.name :
            raise ValueError("Le nom ne peut pas être vide")
        self.name = self.name.lower().capitalize()