# gift_aid_schedule_builder, a script for building gift aid schedules for UK-based
# charities - Copyright (C) 2024  Peter Thomas

from logic import key_cleaning

from unittest import TestCase


class CleanKeyTests(TestCase):

    def test_removes_non_letters(self) -> None:
        unclean_string = "foo &8_\ bar"
        self.assertEqual(
            key_cleaning.clean_key(unclean_string),
            "foobar",
        )

    def test_preserves_capital_letters(self) -> None:
        unclean_string = "fOoBAr"
        self.assertEqual(
            key_cleaning.clean_key(unclean_string),
            "foobar",
        )
