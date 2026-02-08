from dataclasses import dataclass
import pendulum

@dataclass(frozen=True)
class BusinessLimits:
    daily: int = 366
    weekly: int = 52
    monthly: int = 12
    yearly: int = 1


class FrequencyEngine:
    _LIMITS = BusinessLimits()

    def get_occurrences(self, frequency_str, base_now=None):
        tz = pendulum.local_timezone()
        
        try:
            parts = frequency_str.split("@")
            if len(parts) != 3:
                raise ValueError()
                
            start_str, cadence, limit_str = parts
            limit = int(limit_str)
            # Validation de la limite positive
            if limit < 1:
                raise ValueError("La limite doit être >= 1")
            
            # Code simple, lisible, sans concessions pour les tests
            if start_str == "tomorrow":
                current_date = pendulum.tomorrow(tz=tz)
            elif start_str == "today":
                current_date = pendulum.today(tz=tz)
            else:
                current_date = pendulum.parse(start_str, tz=tz)

            # --- APPLICATION DES LIMITES MÉTIER ---
            # On récupère dynamiquement la limite si elle existe dans BusinessLimits
            max_allowed = getattr(self._LIMITS, cadence, None)
            if max_allowed is not None:
                limit = min(limit, max_allowed)
            # --------------------------------------    
            
            occurrences = []
            for i in range(1,limit+1): # on ne prends pas la date de départ
                if cadence == "daily":
                    occurrence = current_date.add(days=i)
                elif cadence == "weekly":
                    occurrence = current_date.add(weeks=i)
                elif cadence == "monthly":
                    occurrence = current_date.add(months=i)
                elif cadence == "yearly":
                    occurrence = current_date.add(years=i)
                else:
                    raise ValueError("Cadence non supportée")
                    
                occurrences.append(occurrence)
                
            return occurrences
            
        except Exception:
            raise ValueError(f"Instruction de fréquence invalide : {frequency_str}")
