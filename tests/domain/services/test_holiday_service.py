import pendulum
import pytest

from todo_bene.domain.services.frequency_engine import FrequencyEngine
from todo_bene.domain.services.holiday_service import HolidayService


def test_holiday_service_france():
    service = HolidayService()
    # 1er Mai 2026 en France
    dt = pendulum.datetime(2026, 5, 1, tz="Europe/Paris")
    assert service.is_holiday(dt) is True
    assert "Fête du Travail" in service.get_holiday_name(dt)

def test_holiday_service_weekend_vs_holiday():
    # Test d'intégration via l'engine
    # Le 1er Janvier 2027 est un Vendredi (Férié)
    # L'engine doit décaler au Lundi 4 Janvier
    service = HolidayService()
    engine_with_service = FrequencyEngine(holiday_service=service)
    
    instruction = "2027-01-01@daily@1|next_workday"
    occ = engine_with_service.get_occurrences(instruction)
    
    assert occ[0].to_date_string() == "2027-01-04"
    assert occ[0].day_of_week == pendulum.MONDAY