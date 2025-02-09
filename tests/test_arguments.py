from unittest import TestCase

import arguments


class ParseArgumentsTests(TestCase):

    def test_parses_legitimate_output_values(self) -> None:
        for value, result in [
            ("excel", arguments.SpreadsheetType.EXCEL),
            ("libre", arguments.SpreadsheetType.LIBRE),
        ]:
            arguments_ = [f"--output={value}"]
            self.assertEqual(
                arguments.parse_arguments(arguments_),
                result,
                msg=f"For value {value}",
            )

    def test_rases_output_value_illegitimate(self) -> None:
        illegitimate_value = "foo"
        with self.assertRaises(arguments.UnexpectedSpreadsheetType) as cm:
            arguments_ = [f"--output={illegitimate_value}"]
            arguments.parse_arguments(arguments_)

        raised_exception: arguments.UnexpectedSpreadsheetType = cm.exception
        self.assertEqual(
            raised_exception.passed_value,
            illegitimate_value,
            msg=f"Passed value was {raised_exception.passed_value}",
        )

    def test_raises_output_value_absent(self) -> None:
        with self.assertRaises(arguments.NoSpreadsheetTypeProvided):
            arguments.parse_arguments([])
