# gift_aid_schedule_builder, a script for building gift aid schedules for UK-based
# charities - Copyright (C) 2024  Peter Thomas

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
