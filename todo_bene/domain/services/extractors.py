# todo_bene/domain/services/extractors.py
import re


class BaseExtractor:
    """Classe parente définissant l'interface et la priorité des extracteurs."""
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


class RelativePositionExtractor(BaseExtractor):
    priority = 15 

    def extract(self, text: str):
        #  On définit les briques élémentaires pour la lisibilité
        POSITIONS = r"last|latest|1er|\d+(?:ème|th|st|nd|rd)"
        TARGETS = r"mon|tue|wed|thu|fri|sat|sun|d|day|workday|workingday"
        PERIODS = r"m|y|q|quarter|s|semester|f|fortnight"

        # 2. On assemble avec le mode VERBOSE pour commenter chaque bloc
        pattern = rf"""
            \b(?P<pos>{POSITIONS})      # Position (ex: last, 1er, 135ème)
            \s+                         # Un ou plusieurs espaces
            (?P<target>{TARGETS})       # Cible (ex: fri, day, workday)
            \s+                         # Un ou plusieurs espaces
            (?P<period>{PERIODS})       # Période (ex: m, quarter, y)
            \b
        """

        match = re.search(pattern, text, re.VERBOSE)
        if match:
            pos = match.group("pos")
            target = match.group("target")
            period = match.group("period")

            # --- Normalisation Position ---
            if pos in ["last", "latest"]:
                pos = "last"
            elif pos in ["1er", "1st"]:
                pos = "1st"
            elif any(pos.endswith(s) for s in ["ème", "st", "nd", "rd", "th"]):
                num_match = re.search(r"\d+", pos)
                if num_match:
                    val = num_match.group()
                    # On force le format technique (ex: 27th, 135th)
                    if val == "1": pos = "1st"
                    elif val == "2": pos = "2nd"
                    elif val == "3": pos = "3rd"
                    else: pos = f"{val}th"
            
            # --- Normalisation Cible ---
            if target == "d": target = "day"

            # --- Normalisation Période (Mapping vers les fréquences) ---
            period_map = {
                "m": "monthly",
                "y": "yearly",
                "q": "quarter",
                "quarter": "quarter",
                "s": "semester",
                "semester": "semester",
                "f": "fortnight",
                "fortnight": "fortnight"
            }
            frequency = period_map.get(period, "yearly")
            
            # Retourne le tuple pour forcer l'infini (∞) par défaut
            return (f"{frequency}#{pos}{target}", "∞")
            
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


class SimpleCadenceExtractor(BaseExtractor):
    """
    Extrait les formes techniques simplifiées issues de la normalisation.
    
    C'est le 'filet de sécurité' qui capture les expressions comme '1 m' ou '5 d'
    lorsque les mots-clés naturels (comme 'chaque') ont été nettoyés.
    Gère les formes orphelines après normalisation (ex: '1 m', '5 d', '1 quarter').
    Ces formes arrivent quand 'every' est absent ou supprimé par les stopwords.
    """
    # priority = 25  # Se déclenche juste après les extracteurs complexes
    
    # def extract(self, text: str):
    #     match = re.search(r"^(?P<num>\d+)\s*(?P<unit>w|d|m|y|quarter|semester|fortnight)$", text.strip())
        
    #     if match:
    #         num = match.group("num")
    #         unit = match.group("unit")
            
    #         type_map = {
    #             "w": "weekly", "d": "daily", "m": "monthly", "y": "yearly",
    #             "quarter": "quarter", "semester": "semester", "fortnight": "fortnight"
    #         }
    #         frequency = type_map.get(unit, "yearly")
            
    #         if num == "1":
    #             pos = "1st"
    #         elif num == "2":
    #             pos = "2nd"
    #         elif num == "3":
    #             pos = "3rd"
    #         else:
    #             pos = f"{num}th"
    #         if unit in ["m", "y", "quarter", "semester"]:
    #             # Cycles longs : on cible le jour (ex: monthly#1stday)
    #             cadence = f"{frequency}#{pos}day"
    #         else:
    #             cadence = f"{frequency}#{num}{unit}"
                
    #         return (cadence, "∞") # Forcer l'infini pour ces cadences
    #     return None
    priority = 25
    def extract(self, text: str):
        # Regex capable de capturer : chiffre + espace + unité technique
        match = re.search(r"^(?P<num>\d+)\s*(?P<unit>w|d|m|y|quarter|semester|fortnight)$", text.strip())
        
        if match:
            num = match.group("num")
            unit = match.group("unit")
            
            
            # Mapping vers les fréquences techniques de ton système
            type_map = {
                "w": "weekly", "d": "daily", "m": "monthly", "y": "yearly",
                "quarter": "quarter", "semester": "semester", "fortnight": "fortnight"
            }
            frequency = type_map.get(unit, "yearly")
            
            # Conversion du chiffre en position ordinale (1 -> 1st, 2 -> 2nd...)
            # Crucial pour le format attendu 'monthly#1stday'
            # Assemblage selon l'unité
            if unit in ["m", "y", "quarter", "semester", "fortnight"]:
                if num == "1": pos = "1st"
                elif num == "2": pos = "2nd"
                elif num == "3": pos = "3rd"
                else: pos = f"{num}th"
                cadence = f"{frequency}#{pos}day"
            else:
                # Cycles courts :
                # Pour d (daily) et w (weekly), on garde le format chiffre+unité (ex: daily#5d)
                cadence = f"{frequency}#{num}{unit}"
                
            return (cadence, "∞")
        return None