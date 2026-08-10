"""Date helpers. Age is never stored — it is always derived at read time
(PRD Ch8.4: "Age (Auto-calculated)")."""

from datetime import date


def calculate_age(date_of_birth: date, *, as_of: date | None = None) -> int:
    today = as_of or date.today()
    age = today.year - date_of_birth.year
    if (today.month, today.day) < (date_of_birth.month, date_of_birth.day):
        age -= 1
    return age
