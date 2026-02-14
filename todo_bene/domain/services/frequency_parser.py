import pendulum
import re
from text_to_num import alpha2digit
from todo_bene.i18n.lexicons import LEXICONS
from todo_bene.domain.services.extractors import *

class FrequencyParser:
    SUPPORTED_LANGUAGES = ["en", "fr"]
    DEFAULT_LANGUAGE = "en"

    def __init__(self, language="en"):
        self.language = language if language in self.SUPPORTED_LANGUAGES else self.DEFAULT_LANGUAGE
        self._lexicon = LEXICONS[self.language]
        self.extractors = [cls() for cls in sorted(BaseExtractor.__subclasses__(), key=lambda x: x.priority)]
    
    def _normalize(self, text: str) -> str:        
        normalized = text.lower().strip()
        
        # 1. D'abord transformer les nombres écrits en lettres (ex: cent trente-cinquième -> 135ème)
        # On fait ça avant le lexique pour ne pas casser les groupes de mots
        normalized = alpha2digit(normalized, lang=self.language, threshold=0) 

        # 2. Substitution via le lexique (ex: 135ème -> 135, jour -> d, année -> y)
        translation_keys = [k for k in self._lexicon.keys() if k != "stopwords"]
        sorted_keys = sorted(translation_keys, key=len, reverse=True)

        for human_word in sorted_keys:
            pattern = r'\b' + re.escape(human_word) + r'\b'
            normalized = re.sub(pattern, self._lexicon[human_word], normalized)
        
        # 3. Nettoyage des stopwords (ex: le, de, l')
        stopwords = self._lexicon.get("stopwords", [])
        for sw in stopwords:
            pattern = r'\b' + re.escape(sw) + r'\b'
            normalized = re.sub(pattern, "", normalized)
            
        return " ".join(normalized.split())

    def _resolve_relative_end(self, period: str) -> str:
        now = pendulum.now(tz=pendulum.local_timezone())
        if period == "w": target = now.end_of('week')
        elif period == "m": target = now.end_of('month')
        elif period == "fortnight": target = now.add(days=14).end_of('day')
        elif period == "quarter": target = now.end_of('quarter')
        elif period == "semester":
            month = 6 if now.month <= 6 else 12
            target = now.replace(month=month).end_of('month')
        elif period == "y": target = now.end_of('year')
        else: return "∞"
        return target.to_date_string()

    def _resolve_fixed_date(self, day_str: str, month_str: str) -> str:
        tz = pendulum.local_timezone()
        try:
            now = pendulum.now(tz=tz)
            day, month = int(day_str), int(month_str)
            target = pendulum.datetime(now.year, month, day, tz=tz)
            if target.to_date_string() < now.to_date_string():
                target = target.add(years=1)
            return target.to_date_string()
        except: return "∞"

    def _resolve_until_logic(self, target_data: str, is_end_of: bool) -> str:
        if is_end_of: return self._resolve_relative_end(target_data.strip())
        date_parts = target_data.split()
        if len(date_parts) == 2: return self._resolve_fixed_date(date_parts[0], date_parts[1])
        return "∞"

    def parse(self, text: str) -> str:
        """
        Transforme une phrase naturelle en chaîne technique de fréquence.
        
        Algorithme :
        1. Normalisation via lexique et conversion chiffres.
        2. Détection des reports (shift).
        3. Extraction des limites (durées 'pendant' ou dates 'jusqu'à').
        4. Nettoyage de la ponctuation traînante.
        5. Passage dans la boucle des extracteurs prioritaires.
        6. Assemblage final.
        """
        # 1. Normalisation
        normalized = self._normalize(text)

        # INITIALISATION DES VARIABLES (Correctif UnboundLocalError)
        cadence_tech = "unknown"
        extractor_limit = None
        
        # 2. Détection du SHIFT
        has_shift = "|shift" in normalized
            
        # 3. Extraction de la LIMITE EXPLICITE (Durée / Date)
        current_limit = None
        duration_pattern = r"(?:for|next)\s+(\d+)\s*(d|w|m|y)|(\d+)\s+(?:for|next)\s*(d|w|m|y)"
        durations = re.findall(duration_pattern, normalized) # @@@ Capture toutes les durées
        
        final_duration = None # @@@
        sequence_duration = None # @@@
        
        for d in durations: # @@@ Arbitrage entre les durées trouvées
            val = d[0] or d[2] # @@@
            unit = d[1] or d[3] # @@@
            if not sequence_duration: # @@@ La première durée définit la séquence (ex: 5 jours)
                sequence_duration = f"+{val}{unit}" # @@@
            final_duration = f"+{val}{unit}" # @@@ La dernière définit la limite globale (ex: 2 semaines)

        current_limit = final_duration # @@@
        normalized = re.sub(duration_pattern, "", normalized)

        # Extraction de la date de fin (Until)
        until_pattern = r"until(?:_end)?\s+([\w/]+(?:\s+[\w/]+)?)"
        until_match = re.search(until_pattern, normalized)
        if until_match:
            is_end_of = "until_end" in until_match.group(0)
            current_limit = self._resolve_until_logic(until_match.group(1), is_end_of)
            normalized = re.sub(until_pattern, "", normalized)

        # # 4. Nettoyage final pour extracteurs
        # # On nettoie les résidus pour que les extracteurs ne reçoivent que la cadence
        clean_text = normalized.replace("|shift", "").replace("next", "")
        clean_text = " ".join(clean_text.split()).strip()
        
        # 5. Extraction de la Cadence
        # Cas particulier : l'utilisateur a juste donné un intervalle (ex: "10 jours")
        is_seq_only = not clean_text and sequence_duration
        """
            Cas où le texte est vide après extraction de la durée (ex: 'Les 5 prochains jours').
            On génère une séquence automatique (1,2,3,4,5).
        """
        
        if is_seq_only:
            # (Logique de séquence conservée telle quelle...)
            unit = sequence_duration[-1]
            count = int(sequence_duration[1:-1])
            days_seq = ",".join(map(str, range(1, count + 1)))
            cadence_tech = f"sequence#{days_seq}{unit}"
            extractor_limit = str(count)
            if current_limit == sequence_duration:
                 current_limit = None
        else:
            """
            Cas général : On nettoie les virgules de ponctuation (ex: '1 m,') 
            puis on interroge chaque extracteur selon sa priorité.
            """
            # --- LE NETTOYAGE CHIRURGICAL ---
            # On supprime les virgules de ponctuation (ex: "1 m,") 
            # MAIS on garde les virgules entre chiffres (ex: "1,2,3")
            # Regex : cherche une virgule qui n'est pas entourée de chiffres
            clean_text_for_ext = re.sub(r'(?<!\d),(?!\d)', ' ', clean_text)
            
            # On compacte les espaces pour avoir une chaîne propre
            clean_text_for_ext = " ".join(clean_text_for_ext.split()).strip()

            # Boucle sur les extracteurs avec le texte nettoyé
            for extractor in self.extractors:
                result = extractor.extract(clean_text_for_ext)
                if result:
                    if isinstance(result, tuple):
                        cadence_tech, extractor_limit = result
                    else:
                        cadence_tech = result
                        # Cas spécial des séquences manuelles pour compter les items
                        if "sequence#" in cadence_tech:
                            items_part = re.sub(r'[dwmy]$', '', cadence_tech.split('#')[1])
                            extractor_limit = str(len(items_part.split(',')))
                    break


        if cadence_tech == "unknown":
            return "unknown"

        # 6. Résolution de la limite finale
        if current_limit:
            final_limit = current_limit
        elif extractor_limit:
            final_limit = extractor_limit
        # Correction : On ne met ∞ que si "every" est présent OU pour les cycles non-hebdomadaires
        # Cela permet à "Lundi et Jeudi" de rester à @1
        elif "every" in normalized or any(cycle in cadence_tech for cycle in ["daily#", "monthly#", "yearly#", "quarter#", "semester#", "fortnight#"]):
            final_limit = "∞"
        else:
            final_limit = "1"


        # 7. Gestion des Exceptions (!)
        exception_part = ""
        MONTHS_MAP = {
        "01": "jan", "02": "feb", "03": "mar", "04": "apr",
        "05": "may", "06": "jun", "07": "jul", "08": "aug",
        "09": "sep", "10": "oct", "11": "nov", "12": "dec"
        }

        if "!" in clean_text:
            raw_exc = clean_text.split("!")[1].strip()
            # On normalise les séparateurs pour éviter sat,,,sun
            words = raw_exc.replace(",", " ").split()
            # On filtre les stopwords
            filtered = [w for w in words if w not in self._lexicon.get("stopwords", [])]
            # Traduction des mois numériques (08 -> aug) ---
            translated = [MONTHS_MAP.get(w, w) for w in filtered]
            if translated:
                exception_part = "!" + ",".join(translated)

        # 8. Assemblage
        shift_suffix = "|next_workday" if has_shift else ""
        return f"today@{cadence_tech}@{final_limit}{exception_part}{shift_suffix}"
