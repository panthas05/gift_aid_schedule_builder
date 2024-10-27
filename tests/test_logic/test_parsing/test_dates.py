# gift_aid_schedule_builder, a script for building gift aid schedules for UK-based
# charities - Copyright (C) 2024  Peter Thomas

from logic.parsing import dates

from unittest import TestCase
from datetime import date


class ParseUkFormattedDateTests(TestCase):
    day = 27
    month = 2
    year = 1997
    test_date = date(
        year,
        month,
        day,
    )

    def test_handles_full_year(self) -> None:
        date_string = f"{self.day}/{self.month}/{self.year}"
        parsed_date = dates.parse_uk_formatted_date(date_string)
        self.assertEqual(
            parsed_date,
            self.test_date,
        )

    def test_handles_partial_year(self) -> None:
        partial_date = f"{self.year}"[2:]
        date_string = f"{self.day}/{self.month}/{partial_date}"
        parsed_date = dates.parse_uk_formatted_date(date_string)
        self.assertEqual(
            parsed_date,
            self.test_date,
        )

    def test_raises_value_error_for_non_uk_format(self) -> None:
        date_string = f"{self.year}-{self.month}-{self.day}"
        with self.assertRaises(ValueError):
            dates.parse_uk_formatted_date(date_string)
