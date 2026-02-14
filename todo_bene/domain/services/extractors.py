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
    # Priorité augmentée (donc passe APRÈS les positions relatives)
    priority = 15 
    def extract(self, text: str):
        # On ancre au début (^) pour éviter de matcher le milieu d'une phrase
        # Mais on ne met pas de $ à la fin pour laisser passer les exceptions (! ...)
        match = re.search(r"^every\s*(?P<num>\d+)?\s*(?P<unit>[wdmy])\b", text.strip())
        
        if match:
            num = match.group("num") or "1"
            unit = match.group("unit")
            type_map = {"w": "weekly", "d": "daily", "m": "monthly", "y": "yearly"}
            return (f"{type_map[unit]}#{num}{unit}", "∞")
        return None

class MultiDayExtractor(BaseExtractor):
    """Gère 'Lundi et Jeudi' (Limite par défaut : 1)."""
    priority = 12
    def extract(self, text: str):
        # Si le texte contient une exception, cet extracteur ne doit pas gérer les jours qui sont après le !
        if "!" in text:
            # On ne regarde que ce qui est AVANT le !
            text = text.split("!")[0]
        days_pattern = r"(mon|tue|wed|thu|fri|sat|sun)"
        found_days = re.findall(days_pattern, text)
        if len(found_days) > 1:
            days_str = ",".join(found_days)
            # Pas de tuple ici -> le parser utilisera la limite par défaut (1)
            return f"weekly#1{days_str}"
        return None

class YearlySpecificMonthExtractor(BaseExtractor):
    """Gère '1 mon 10' -> yearly#1stmon@oct"""
    priority = 14
    
    def extract(self, text: str):
        MONTHS_MAP = {
            "01": "jan", "1": "jan", "02": "feb", "2": "feb", "03": "mar", "3": "mar",
            "04": "apr", "4": "apr", "05": "may", "5": "may", "06": "jun", "6": "jun",
            "07": "jul", "7": "jul", "08": "aug", "8": "aug", "09": "sep", "9": "sep",
            "10": "oct", "11": "nov", "12": "dec"
        }
        
        MONTHS_REGEX = r"01|02|03|04|05|06|07|08|09|10|11|12|[1-9]"
        POSITIONS = r"last|1|2|3|\d+"
        DAYS = r"mon|tue|wed|thu|fri|sat|sun"
        
        pattern = rf"^(?P<pos>{POSITIONS})\s+(?P<day>{DAYS})\s+(?P<month>{MONTHS_REGEX})$"
        match = re.search(pattern, text)
        
        if match:
            pos_raw = match.group("pos")
            day = match.group("day")
            month_num = match.group("month")
            
            # 1. Normalisation position
            if pos_raw == "1": pos = "1st"
            elif pos_raw == "2": pos = "2nd"
            elif pos_raw == "3": pos = "3rd"
            elif pos_raw == "last": pos = "last"
            else: pos = f"{pos_raw}th"
            
            # 2. Conversion chiffre -> code (ex: 10 -> oct)
            month_code = MONTHS_MAP.get(month_num, "jan")
            
            # 3. Retour du tuple avec Cadence + Limite
            # On ajoute un second '@∞' pour forcer la structure attendue
            return (f"yearly#{pos}{day}@{month_code}", "∞")
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
    """Gère les positions relatives : '2nd workday m', '135 d y', 'last fri m'."""
    # Priorité diminuée (donc passe AVANT les intervalles simples)
    priority = 10 

    def extract(self, text: str):
        p_pos = r"(?P<pos>last|latest|\d+(?:ème|th|st|nd|rd)?)"
        p_target = r"(?P<target>workday|workingday|non_workday|day|d|mon|tue|wed|thu|fri|sat|sun)"
        # On s'assure que 'every' optionnel est bien géré au milieu
        p_period = r"(?:every\s+)?(?P<period>y|m|w|d|quarter|semester|fortnight)"

        pattern = rf"{p_pos}\s*{p_target}\s*{p_period}"
        
        match = re.search(pattern, text)
        if match:
            pos_raw = match.group("pos")
            target_raw = match.group("target")
            period_raw = match.group("period")

            # Mappage de la période
            period_map = {
                "y": "yearly", "m": "monthly", "w": "weekly", "d": "daily",
                "quarter": "quarter", "semester": "semester", "fortnight": "fortnight"
            }
            period = period_map.get(period_raw, "monthly")

            # Normalisation de la cible (ex: 'd' doit redevenir 'day' techniquement)
            target = "day" if target_raw == "d" else target_raw

            # Normalisation de la position (chiffre -> 1st, 2nd, nth)
            if pos_raw in ["last", "latest"]:
                pos = "last"
            else:
                num_str = re.sub(r"\D", "", pos_raw)
                if not num_str: return None
                n = int(num_str)
                if n == 1: pos = "1st"
                elif n == 2: pos = "2nd"
                elif n == 3: pos = "3rd"
                else: pos = f"{n}th"

            return f"{period}#{pos}{target}"
            
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