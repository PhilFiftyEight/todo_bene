from dataclasses import dataclass


@dataclass(frozen=True)
class Category:
    name: str

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
        # Règle de domaine : une catégorie doit avoir un nom non vide
        if not self.name or self.name.strip() == "":
            raise ValueError("Le nom ne peut pas être vide")