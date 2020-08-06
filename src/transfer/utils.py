from datetime import date


def add_month(d: date, original_day: int = None):
    if d.month == 12:
        # January is 31 days long, so no additional checks for day needed
        return d.replace(year=d.year + 1, month=1)

    day = d.day if original_day is None else original_day
    while True:
        try:
            return d.replace(month=d.month + 1, day=day)
        except ValueError:
            day -= 1
