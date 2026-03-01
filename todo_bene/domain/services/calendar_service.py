import pendulum
from todo_bene.domain.services.holiday_service import HolidayService


def is_send_day(dt: pendulum.DateTime, business_days_only: bool) -> bool:
    """
    Vérifie si l'envoi est autorisé en utilisant le HolidayService.
    """
    if not business_days_only:
        return True
        
    # 1. Vérification Week-end (Pendulum: 6=Samedi, 7=Dimanche)
    if dt.day_of_week in [pendulum.SATURDAY, pendulum.SUNDAY]:
        return False
        
    # 2. Vérification Jours Fériés via le service existant
    holiday_service = HolidayService()
    if holiday_service.is_holiday(dt):
        return False
        
    return True