# todo_bene/domain/services/extractors.py
import re

class BaseExtractor:
    priority = 100
    description = "Base extractor"
    example = ""

    def extract(self, text: str):
        raise NotImplementedError("Chaque extracteur doit implémenter la méthode extract.")

class NextOccurrencesExtractor(BaseExtractor):
    """Gère 'Les 5 prochains jours', 'Next 3 weeks'."""
    priority = 5
    def extract(self, text: str):
        if text.strip().startswith("every"):
            return None
            
        match = re.search(r"(?P<num>\d+)\s*next\s*(?P<unit>[wdmy])\b|next\s*(?P<num2>\d+)\s*(?P<unit2>[wdmy])\b", text)
        if match:
            num = int(match.group("num") or match.group("num2"))
            unit = match.group("unit") or match.group("unit2")
            
            steps = ",".join(str(i) for i in range(1, num + 1))
            return f"sequence#{steps}{unit}"
            
        return None

class SimpleIntervalExtractor(BaseExtractor):
    """Gère 'Chaque jour' (∞) ou 'Toutes les 3 semaines' (∞)."""
    priority = 10
    def extract(self, text: str):
        match = re.search(r"every\s*(?P<num>\d+)?\s*(?P<unit>[wdmy])\b", text)
        if match:
            num = match.group("num") or "1"
            unit = match.group("unit")
            type_map = {"w": "weekly", "d": "daily", "m": "monthly", "y": "yearly"}
            # Ici, l'intention "Chaque/Tous" implique l'infini
            return (f"{type_map[unit]}#{num}{unit}", "∞")
        return None

class MultiDayExtractor(BaseExtractor):
    """Gère 'Lundi et Jeudi' (Limite par défaut : 1)."""
    priority = 12
    def extract(self, text: str):
        days_pattern = r"(mon|tue|wed|thu|fri|sat|sun)"
        found_days = re.findall(days_pattern, text)
        if len(found_days) > 1:
            days_str = ",".join(found_days)
            # Pas de tuple ici -> le parser utilisera la limite par défaut (1)
            return f"weekly#1{days_str}"
        return None

class SpecificDayExtractor(BaseExtractor):
    """Gère 'Tous les lundis' (∞)."""
    priority = 15
    def extract(self, text: str):
        days_pattern = r"(mon|tue|wed|thu|fri|sat|sun)"
        match = re.search(fr"every\s*{days_pattern}", text)
        if match:
            day = match.group(1)
            # "Tous les" implique l'infini
            return (f"weekly#1{day}", "∞")
        return None

class SequenceExtractor(BaseExtractor):
    """Gère '1, 2, 4 jours' (Limite par défaut : 1)."""
    priority = 20
    def extract(self, text: str):
        match = re.search(r"(?P<seq>[\d\s,]+)\s*(?P<unit>[wdmy])$", text)
        if match and "," in match.group("seq"):
            raw_seq = match.group("seq").replace(" ", "").strip(",")
            unit = match.group("unit")
            return f"sequence#{raw_seq}{unit}"
        return None
