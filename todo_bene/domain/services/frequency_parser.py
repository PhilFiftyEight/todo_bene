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
        translation_keys = [k for k in self._lexicon.keys() if k != "stopwords"]
        sorted_keys = sorted(translation_keys, key=len, reverse=True)

        for human_word in sorted_keys:
            pattern = r'\b' + re.escape(human_word) + r'\b'
            normalized = re.sub(pattern, self._lexicon[human_word], normalized)
        
        normalized = alpha2digit(normalized, lang=self.language, threshold=0) 
        stopwords = self._lexicon.get("stopwords", [])
        for sw in stopwords:
            pattern = r'\b' + re.escape(sw) + r'\b'
            normalized = re.sub(pattern, "", normalized)
        return " ".join(normalized.split())

    def _resolve_relative_end(self, period: str) -> str:
        now = pendulum.now(tz=pendulum.local_timezone())
        
        if period == "w": 
            target = now.end_of('week')
        elif period == "m": 
            target = now.end_of('month')
        elif period == "fortnight": 
            # La fin de la quinzaine est souvent vue comme le 14ème jour
            target = now.add(days=14).end_of('day')
        elif period == "quarter": 
            target = now.end_of('quarter')
        elif period == "semester":
            # Fin juin ou fin décembre
            month = 6 if now.month <= 6 else 12
            target = now.replace(month=month).end_of('month')
        elif period == "y": 
            target = now.end_of('year')
        else:
            return "∞"
            
        return target.to_date_string()

    def _resolve_fixed_date(self, day_str: str, month_str: str) -> str:
        tz=pendulum.local_timezone()
        try:
            now = pendulum.now(tz=tz)
            day, month = int(day_str), int(month_str)
            target = pendulum.datetime(now.year, month, day, tz=tz)
            
            if target.to_date_string() < now.to_date_string():
                target = target.add(years=1)
                
            return target.to_date_string()
        except:
            return "∞"

    def parse(self, text: str, start_date="today", limit="1") -> str:
        normalized = self._normalize(text)
        for extractor in self.extractors:
            result = extractor.extract(normalized)
            if result:
                cadence_tech, current_limit = result if isinstance(result, tuple) else (result, limit)
                
                # --- 1. DURÉE (FOR/NEXT) ---
                matches = list(re.finditer(r"(?P<kw>for|next)\s*(?P<val>\d+)\s*(?P<unit>[wdmy])\b|(?P<val2>\d+)\s*(?P<kw2>for|next)\s*(?P<unit2>[wdmy])\b", normalized))
                if matches:
                    best = next((m for m in matches if (m.group("kw") or m.group("kw2")) == "for"), matches[0])
                    val = best.group("val") or best.group("val2")
                    unit = best.group("unit") or best.group("unit2")
                    kw = best.group("kw") or best.group("kw2")
                    current_limit = val if kw == "next" and "sequence#" in cadence_tech else f"+{val}{unit}"

                # --- 2. DATE DE FIN (Cas n°7) ---
                end_rel_match = re.search(r"until_end\s+(?P<p>w|m|y|quarter|fortnight|semester)", normalized)
                if end_rel_match:
                    current_limit = self._resolve_relative_end(end_rel_match.group("p"))
                
                end_fix_match = re.search(r"until\s+(?P<d>\d{1,2})\s+(?P<m>\d{1,2})", normalized)
                if end_fix_match:
                    current_limit = self._resolve_fixed_date(end_fix_match.group("d"), end_fix_match.group("m"))

                # --- 3. EXCEPTIONS (Cas n°8.1) ---
                exception_part = ""
                if "!" in normalized:
                    # On récupère tout ce qui suit le premier "!"
                    raw_exception = normalized.split("!", 1)[1]
                    # On cherche les jours abrégés (mon, tue, etc.)
                    days_found = re.findall(r"(mon|tue|wed|thu|fri|sat|sun)\b", raw_exception)
                    if days_found:
                        exception_part = f"!{','.join(days_found)}"

                # --- 4. SÉQUENCES ---
                if "sequence#" in cadence_tech and current_limit == "1":
                    current_limit = str(cadence_tech.count(',') + 1)

                return f"{start_date}@{cadence_tech}@{current_limit}{exception_part}"
        return "unknown"