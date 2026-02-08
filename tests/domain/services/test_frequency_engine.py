import pytest
import pendulum
from todo_bene.domain.services.frequency_engine import FrequencyEngine

@pytest.fixture
def engine():
    return FrequencyEngine()

# --- TEST DES CADENCES (La logique Pendulum) ---
@pytest.mark.parametrize("freq_str, base_date, expected_dates", [
    # "2026-03-22@monthly@3" -> On veut les 3 mois SUIVANTS
    (
        "2026-03-22@monthly@3", 
        None, 
        ["2026-04-22", "2026-05-22", "2026-06-22"]
    ),
    # Cas "tomorrow" @daily@2 (Aujourd'hui = 01/01, Tomorrow = 02/01)
    # Répétition 1 = 03/01, Répétition 2 = 04/01
    (
        "tomorrow@daily@2", 
        pendulum.datetime(2026, 1, 1), 
        ["2026-01-03", "2026-01-04"]
    ),
     # Test fin de mois (Jan 31 -> Fév 28 -> Avr 30)
    (
        "2026-01-31@monthly@3", 
        None, 
        ["2026-02-28", "2026-03-31", "2026-04-30"]
    ),   
    # Ton cas Yearly bissextile (29 Fév 2024 @ 1)
    (
        "2024-02-29@yearly@1", 
        None, 
        ["2025-02-28"] 
    )
])
def test_frequency_engine_cadence_logic(engine, freq_str, base_date, expected_dates):
    # Si on a une base_date, on voyage dans le temps
    if base_date:
        pendulum.travel_to(base_date, freeze=True)
    try:
        occurrences = engine.get_occurrences(freq_str, base_now=base_date)
    
        assert len(occurrences) == len(expected_dates)
        for i, date_str in enumerate(expected_dates):
            assert occurrences[i].to_date_string() == date_str
    finally:
        pendulum.travel_back()

# --- TEST DES LIMITES (Le Tableau Métier) ---
@pytest.mark.parametrize("freq_str, expected_count", [
    # Yearly : "only single duplicate" -> Max 1
    ("2026-01-01@yearly@5", 1), 
    
    # Daily : Max 366 (1 an)
    ("2026-01-01@daily@500", 366),
    
    # Weekly : Max 52 (1 an)
    ("2026-01-01@weekly@100", 52),
    
    # Monthly : Max 12 (1 an)
    ("2026-01-01@monthly@24", 12),
])
def test_frequency_engine_business_limits(engine, freq_str, expected_count):
    occurrences = engine.get_occurrences(freq_str)
    assert len(occurrences) == expected_count

# --- TEST DES CAS D'ERREURS (Fail-Fast) ---
@pytest.mark.parametrize("invalid_str", [
    "2026-03-22@unknown@3",   # Cadence invalide
    "2026-03-22@monthly@X",   # Limite non numérique
    "wrong-date@daily@1",     # Date invalide
    "2026-03-22@monthly@-1",  # Limite négative
    "2026-03-22@monthly",     # Format incomplet
])
def test_frequency_engine_parsing_errors(engine, invalid_str):
    with pytest.raises(ValueError) as excinfo:
        engine.get_occurrences(invalid_str)
    assert "Instruction de fréquence" in str(excinfo.value)
