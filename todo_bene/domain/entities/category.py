from dataclasses import dataclass
from uuid import UUID


@dataclass
class Category:
    name: str
    user_id: UUID
    emoji: str = "🏷️"  # Fallback par défaut

    # Constantes
    QUOTIDIEN = "Quotidien"
    TRAVAIL = "Travail"
    LOISIRS = "Loisirs"
    SPORT = "Sport"
    MEDICAL = "Médical"
    FAMILLE = "Famille"

    ALL = [QUOTIDIEN, TRAVAIL, LOISIRS, SPORT, MEDICAL, FAMILLE]

    # Mapping statique pour l'attribution automatique
    _DEFAULT_MAPPING = {
        QUOTIDIEN: "🏠",
        TRAVAIL: "💼",
        LOISIRS: "🎮",
        SPORT: "🏃",
        MEDICAL: "🩺",
        FAMILLE: "🧑‍🧑‍🧒‍🧒"
    }

    def __post_init__(self):
        # Formatage existant
        self.name = self.name.strip()
        if not self.name:
            raise ValueError("Le nom ne peut pas être vide")
        self.name = self.name.lower().capitalize()
        
        # Attribution automatique de l'émoji selon le nom (KISS)
        if self.name in self._DEFAULT_MAPPING:
            self.emoji = self._DEFAULT_MAPPING[self.name]
