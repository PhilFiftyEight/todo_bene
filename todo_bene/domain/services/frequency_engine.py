from dataclasses import dataclass
import re

import pendulum

from todo_bene.domain.services.holiday_service import HolidayService


@dataclass(frozen=True)
class BusinessLimits:
    daily: int = 366
    fortnight: int = 26 # Quinzaine
    weekly: int = 52
    monthly: int = 12
    quarter: int = 4
    semester: int = 2
    yearly: int = 1

class FrequencyEngine:
    _LIMITS = BusinessLimits()

    def __init__(self, limits=None, holiday_service=None):
        self._LIMITS = limits or BusinessLimits()
        self.holiday_service = holiday_service or HolidayService()

    def _shift_to_workday(self, dt):
        curr = dt
        while curr.day_of_week in [5, 6] or self.holiday_service.is_holiday(curr):
            curr = curr.add(days=1)
        return curr

    def get_occurrences(self, frequency_str, base_now=None):
        tz = pendulum.local_timezone()
        days_map = {"mon":0,"tue":1,"wed":2,"thu":3,"fri":4,"sat":5,"sun":6}
        
        try:
            # 1. Split & Clean
            main_part = frequency_str.split('|')[0].split('!')[0]
            parts = main_part.split("@")
            if len(parts) < 3:
                raise ValueError("Format incomplet")
            start_str, cadence_full = parts[0], parts[1]

            # --- VALIDATION CADENCE ---
            c_parts = cadence_full.split('#')
            base = c_parts[0]
            valid_bases = ["daily", "weekly", "monthly", "yearly", "fortnight", "quarter", "semester", "sequence"]
            if base not in valid_bases:
                raise ValueError(f"Instruction de fréquence : Cadence inconnue {base}")

            # --- PARSING DES SEGMENTS (Unique et Strict) ---
            limit_attr = None
            end_date = None
            target_month = None
            temp_duration = None
            months_list = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]

            for p in parts[2:]:
                if not p: continue
                p_low = p.lower()
                
                if p_low[:3] in months_list:
                    target_month = months_list.index(p_low[:3]) + 1
                elif p == "∞":
                    limit_attr = None
                elif p.isdigit() or (p.startswith('-') and p[1:].isdigit()):
                    val = int(p)
                    if val < 0:
                        raise ValueError("Instruction de fréquence : Limite négative")
                    limit_attr = val
                elif p.startswith("+"):
                    match = re.search(r'(\d+)([dwmy])', p)
                    if match:
                        val, unit = int(match.group(1)), match.group(2)
                        mapping = {'d':'days','w':'weeks','m':'months','y':'years'}
                        temp_duration = (val, mapping.get(unit, 'days'))
                    else:
                        raise ValueError(f"Instruction de fréquence : Durée invalide [{p}]")
                elif p.count("-") >= 2 and len(p) >= 8:
                    end_date = pendulum.parse(p).replace(tzinfo=tz).end_of('day')
                else:
                    raise ValueError(f"Instruction de fréquence : Segment inconnu [{p}]")
            
            # --- START DATE ---
            if start_str == "today": 
                start_date = (base_now or pendulum.now(tz)).start_of('day')
            elif start_str == "tomorrow": 
                start_date = (base_now or pendulum.now(tz)).add(days=1).start_of('day')
            else: 
                start_date = pendulum.parse(start_str).replace(tzinfo=tz).start_of('day')

            if target_month:
                start_date = start_date.replace(month=target_month, day=1)

            # Application de la durée relative si détectée (@+2w)
            if temp_duration:
                end_date = start_date.add(**{temp_duration[1]: temp_duration[0]})

            # --- AJUSTEMENT DE LA LIMITE ---
            max_limit = getattr(self._LIMITS, base, 366)
            interval = int(re.search(r'\d+', c_parts[1]).group()) if (len(c_parts)>1 and re.search(r'\d+', c_parts[1])) else 1
            spec_days = re.findall(r'(mon|tue|wed|thu|fri|sat|sun)', cadence_full)
            
            # Correction RJQ : On assure au moins 1 itération si un intervalle ordinal est fourni (ex: #135)
            base_iterations = max(1, max_limit // interval) if interval > 0 else max_limit
            
            if limit_attr is None:
                final_limit = base_iterations
            else:
                # Calcul de la demande utilisateur (cycles vs jours)
                if base == "weekly" and len(spec_days) > 1:
                    user_requested = limit_attr * len(spec_days)
                else:
                    user_requested = limit_attr
                
                if end_date:
                    final_limit = base_iterations
                else:
                    final_limit = min(user_requested, base_iterations)

            # --- GÉNÉRATION ---
            occurrences = []
            
            if base == "weekly" and spec_days:
                target_wd = [days_map[d] for d in spec_days]
                curr = start_date.add(days=1)
                while len(occurrences) < final_limit:
                    if curr.day_of_week in target_wd:
                        if not end_date or curr <= end_date:
                            occurrences.append(curr)
                        else: break
                    curr = curr.add(days=1)
                    if (curr - start_date).days > 366: break
            
            # Séquences explicites (ex: 1,2,4,8d)
            elif base == "sequence":
                offsets = [int(n) for n in re.findall(r'\d+', cadence_full)]
                unit_char = re.search(r'[dwmy]', cadence_full)
                unit = {'d':'days','w':'weeks','m':'months','y':'years'}.get(unit_char.group(), 'days') if unit_char else 'days'
                
                # Déterminer la taille du saut de cycle (par défaut 1 semaine si on parle de jours)
                cycle_step = 7 if unit == 'days' else 1
                
                idx = 0
                cycle_count = 0
                while len(occurrences) < final_limit:
                    # On calcule l'indice dans la liste d'offsets
                    current_idx = idx % len(offsets)
                    
                    # Si on recommence la liste, on change de cycle
                    if idx > 0 and current_idx == 0:
                        cycle_count += 1
                        
                    # Calcul de la date : Start + (Nombre de cycles * Step) + Offset du jour dans le cycle
                    total_offset = (cycle_count * cycle_step) + offsets[current_idx]
                    
                    occ = start_date.add(**{unit: total_offset})
                    
                    if end_date and occ > end_date:
                        break
                        
                    occurrences.append(occ)
                    idx += 1
                    
                    # Sécurité pour ne pas boucler à l'infini
                    if (occ - start_date).days > 366:
                        break

            else:
                for i in range(1, final_limit + 1):
                    step = i * interval
                    if base == "daily": occ = start_date.add(days=step)

                    elif base == "weekly": occ = start_date.add(weeks=step)

                    elif base == "monthly":
                        # On sépare pour ne pas matcher "mon" dans "monthly"
                        cadence_only = cadence_full.split('#')[1] if '#' in cadence_full else ""
                        is_ordinal = ("workday" in cadence_full or 
                                     "last" in cadence_full or
                                     "day" in cadence_full or 
                                     re.search(r'\d+(st|nd|rd|th)', cadence_full))
                        
                        if is_ordinal:
                            if "workday" in cadence_full:
                                target_count = interval
                                found_count = 0
                                curr = start_date.add(months=i-1).start_of('month')
                                target_month = curr.month
                                while found_count < target_count:
                                    if curr.day_of_week < 5 and not self.holiday_service.is_holiday(curr):
                                        found_count += 1
                                    if found_count == target_count:
                                        occ = curr
                                        break
                                    curr = curr.add(days=1)
                                    if curr.month != target_month:
                                        occ = None
                                        break
                            elif "last" in cadence_full:
                                # Correction RJQ : Recherche le jour uniquement dans cadence_only
                                day_name = re.search(r'(mon|tue|wed|thu|fri|sat|sun)', cadence_only)
                                curr = start_date.add(months=i-1).end_of('month').start_of('day')
                                if day_name:
                                    target_wd = days_map[day_name.group()]
                                    while curr.day_of_week != target_wd:
                                        curr = curr.subtract(days=1)
                                occ = curr
                            else:
                                anchor_day = interval
                                potential_occ = start_date.add(months=i-1).replace(day=anchor_day)
                                if i == 1 and potential_occ < start_date:
                                    occ = start_date.add(months=i).replace(day=anchor_day)
                                else:
                                    occ = potential_occ
                        else:
                            occ = start_date.add(months=i * interval)
                    
                    elif base == "yearly":
                        # Détection d'un ordinal (ex: 1stmon, lastfri)
                        day_name = re.search(r'(mon|tue|wed|thu|fri|sat|sun)', cadence_full)
                        
                        if "last" in cadence_full:
                            # Logique pour "Le dernier [jour] de la période"
                            if target_month:
                                curr = start_date.end_of('month').start_of('day')
                            else:
                                curr = start_date.end_of('year').start_of('day')
                                
                            if day_name:
                                target_wd = days_map[day_name.group()]
                                while curr.day_of_week != target_wd:
                                    curr = curr.subtract(days=1)
                            occ = curr
                        elif day_name and re.search(r'\d+', cadence_full):
                            # Logique pour "Le Nième [jour]" (ex: 1stmon)
                            target_count = interval
                            found_count = 0
                            curr = start_date.start_of('month')
                            target_wd = days_map[day_name.group()]
                            
                            while found_count < target_count:
                                if curr.day_of_week == target_wd:
                                    found_count += 1
                                if found_count == target_count:
                                    occ = curr
                                    break
                                curr = curr.add(days=1)
                        else:
                            # Cas standard ou mois spécifique simple (ex: @oct)
                            if target_month:
                                occ = start_date.add(years=i-1)
                            else:
                                occ = start_date.add(days=step - 1) if interval > 1 else start_date.add(years=step)
 
                    elif base == "fortnight":
                        occ = start_date.add(days=step * 14)

                    elif base == "quarter": 
                        if "last" in cadence_full:
                            # Logique pour "Le dernier [jour] du trimestre"
                            day_name = re.search(r'(mon|tue|wed|thu|fri|sat|sun)', cadence_full)
                            current_quarter_end_month = ((start_date.month - 1) // 3 + i) * 3
                            curr = start_date.replace(month=current_quarter_end_month).end_of('month').start_of('day')
                            
                            if day_name:
                                target_wd = days_map[day_name.group()]
                                while curr.day_of_week != target_wd:
                                    curr = curr.subtract(days=1)
                            occ = curr
                        else:
                            occ = start_date.add(days=step - 1) if interval > 1 else start_date.add(months=step * 3)

                    elif base == "semester": 
                        occ = start_date.add(days=step - 1) if interval > 1 else start_date.add(months=step * 6)

                    else: occ = start_date.add(days=step)
                    
                    if end_date and occ > end_date:
                        break

                    if limit_attr is None and base == "daily" and (occ - start_date).days >= 365:
                        occurrences.append(occ)
                        break

                    occurrences.append(occ)

            # --- POST-PROCESS ---
            if '!' in frequency_str:
                months_map = {
                    "jan":1, "feb":2, "mar":3, "apr":4, "may":5, "jun":6,
                    "jul":7, "aug":8, "sep":9, "oct":10, "nov":11, "dec":12
                }
                raw_exclusions = frequency_str.split('!')[1].split(',')
                
                excl_days = [days_map[d.strip()] for d in raw_exclusions if d.strip() in days_map]
                excl_months = [months_map[m.strip()] for m in raw_exclusions if m.strip() in months_map]
                
                if excl_days:
                    occurrences = [o for o in occurrences if o.day_of_week not in excl_days]
                if excl_months:
                    occurrences = [o for o in occurrences if o.month not in excl_months]

            # Rétablissement des décalages de jours ouvrés (Pipe '|')
            if '|' in frequency_str and "next_workday" in frequency_str:
                occurrences = [self._shift_to_workday(o) for o in occurrences]

            return sorted(list(set(occurrences)))[:final_limit]

        except Exception as e:
            raise ValueError(f"Instruction de fréquence invalide (Instruction de fréquence) : {str(e)}")
