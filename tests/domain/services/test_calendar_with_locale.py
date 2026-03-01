import pendulum
from todo_bene.domain.services.calendar_service import is_send_day

def test_is_send_day_with_paris_locale():
    # Lundi de Pâques 2026 en France (6 Avril)
    # On force la timezone pour que le HolidayService détecte 'FR'
    easter_monday = pendulum.datetime(2026, 4, 6, tz='Europe/Paris')
    
    # Un mardi normal (7 Avril 2026)
    normal_tuesday = pendulum.datetime(2026, 4, 7, tz='Europe/Paris')
    
    # Un dimanche (5 Avril 2026)
    sunday = pendulum.datetime(2026, 4, 5, tz='Europe/Paris')

    # Assertions en mode business_days_only=True
    assert is_send_day(easter_monday, True) is False  # Férié FR
    assert is_send_day(sunday, True) is False         # Week-end
    assert is_send_day(normal_tuesday, True) is True  # Jour ouvré
    
    # Assertion en mode business_days_only=False
    assert is_send_day(easter_monday, False) is True