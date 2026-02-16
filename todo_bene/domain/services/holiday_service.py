import pendulum
import holidays
from typing import Optional

class HolidayService:
    _TZ_COUNTRY_MAP = {
        'Europe/Paris': 'FR',
        'Europe/London': 'GB',
        'America/New_York': 'US',
        'Europe/Brussels': 'BE',
        'Europe/Zurich': 'CH',
        # Extensible facilement
    }

    def __init__(self, default_country: str = 'US'):
        self.default_country = default_country
        self._cache = {}

    def get_country_code(self, tz_name: str) -> str:
        """Déduit le code pays à partir du nom du timezone."""
        return self._TZ_COUNTRY_MAP.get(tz_name, self.default_country)

    def is_holiday(self, dt: pendulum.DateTime) -> bool:
        """Vérifie si une date donnée est un jour férié."""
        country = self.get_country_code(dt.timezone_name)
        year = dt.year
        
        # Cache pour éviter de re-instancier holidays à chaque appel
        cache_key = f"{country}_{year}"
        if cache_key not in self._cache:
            try:
                self._cache[cache_key] = holidays.country_holidays(country, years=year)
            except Exception:
                self._cache[cache_key] = {}

        return dt in self._cache[cache_key]

    def get_holiday_name(self, dt: pendulum.DateTime) -> Optional[str]:
        """Retourne le nom du jour férié si applicable."""
        if self.is_holiday(dt):
            country = self.get_country_code(dt.timezone_name)
            return holidays.country_holidays(country).get(dt)
        return None