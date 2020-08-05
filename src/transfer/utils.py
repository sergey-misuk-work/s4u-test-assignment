from datetime import date


def add_month(d: date):
    if d.month == 12:
        return d.replace(year=d.year + 1, month=1)

    day = d.day
    while True:
        try:
            return d.replace(month=d.month + 1, day=day)
        except ValueError:
            day -= 1
