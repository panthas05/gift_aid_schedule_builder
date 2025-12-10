from datetime import date, datetime


def parse_uk_formatted_date(date_string: str) -> date:
    try:
        return datetime.strptime(
            date_string,
            "%d/%m/%Y",
        ).date()
    except ValueError:
        return datetime.strptime(
            date_string,
            "%d/%m/%y",
        ).date()
