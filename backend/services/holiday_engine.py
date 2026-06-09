import datetime
from typing import List, Dict

class HolidayEngine:
    FIXED_HOLIDAYS = [
        {"month": 1, "day": 1, "name": "Nouvel An"},
        {"month": 1, "day": 11, "name": "Manifeste de l'Indépendance"},
        {"month": 5, "day": 1, "name": "Fête du Travail"},
        {"month": 7, "day": 30, "name": "Fête du Trône"},
        {"month": 8, "day": 14, "name": "Allégeance Oued Eddahab"},
        {"month": 8, "day": 20, "name": "Révolution du Roi et du Peuple"},
        {"month": 8, "day": 21, "name": "Fête de la Jeunesse"},
        {"month": 11, "day": 6, "name": "Marche Verte"},
        {"month": 11, "day": 18, "name": "Fête de l'Indépendance"},
    ]

    # For a real implementation, we could query https://date.nager.at/api/v3/PublicHolidays/{year}/MA
    # or generate approximate hijri dates. Here we mock some hijri for 2026/2027 to avoid API dependency limits.
    HIJRI_MOCKS_2026 = [
        {"month": 3, "day": 20, "name": "Aïd al-Fitr (Estimé)"},
        {"month": 5, "day": 27, "name": "Aïd al-Adha (Estimé)"},
        {"month": 6, "day": 17, "name": "1er Moharram (Estimé)"},
        {"month": 8, "day": 26, "name": "Aïd al-Mawlid (Estimé)"},
    ]

    @classmethod
    def get_upcoming_holidays(cls, days_ahead: int = 60) -> List[Dict]:
        today = datetime.date.today()
        upcoming = []
        
        # Check fixed holidays for this year and next year
        for year in [today.year, today.year + 1]:
            for hol in cls.FIXED_HOLIDAYS:
                hol_date = datetime.date(year, hol["month"], hol["day"])
                if today <= hol_date <= today + datetime.timedelta(days=days_ahead):
                    upcoming.append({
                        "date": hol_date,
                        "name": hol["name"],
                        "is_fixed": True
                    })
                    
            if year == 2026:
                for hol in cls.HIJRI_MOCKS_2026:
                    hol_date = datetime.date(year, hol["month"], hol["day"])
                    if today <= hol_date <= today + datetime.timedelta(days=days_ahead):
                        upcoming.append({
                            "date": hol_date,
                            "name": hol["name"],
                            "is_fixed": False
                        })

        upcoming.sort(key=lambda x: x["date"])
        return upcoming

holiday_engine = HolidayEngine()
