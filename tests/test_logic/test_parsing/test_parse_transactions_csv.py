# gift_aid_schedule_builder, a script for building gift aid schedules for UK-based
# charities - Copyright (C) 2024  Peter Thomas

from logic.parsing import parse_transactions_csv

import csv
import errno
from datetime import date
from decimal import Decimal, InvalidOperation
import os
import pathlib
from unittest import TestCase


class ParseTransactionsAmountTests(TestCase):

    def test_handles_blank_price(self) -> None:
        self.assertEqual(
            parse_transactions_csv._parse_transaction_amount(""),
            None,
        )

    def test_handles_blank_price_as_hyphens(self) -> None:
        self.assertEqual(
            parse_transactions_csv._parse_transaction_amount("--"),
            None,
        )

    def test_parses_valid_positive_price_with_currency_symbol(self) -> None:
        self.assertEqual(
            parse_transactions_csv._parse_transaction_amount("£5.00"),
            Decimal("5.00"),
        )

    def test_parses_valid_positive_price_without_currency_symbol(self) -> None:
        self.assertEqual(
            parse_transactions_csv._parse_transaction_amount("5.00"),
            Decimal("5.00"),
        )

    def test_parses_valid_positive_price_without_decimal_places(self) -> None:
        self.assertEqual(
            parse_transactions_csv._parse_transaction_amount("5"),
            Decimal("5.00"),
        )

    def test_parses_valid_negative_price_with_currency_symbol(self) -> None:
        self.assertEqual(
            parse_transactions_csv._parse_transaction_amount("£-5.00"),
            Decimal("-5.00"),
        )
        self.assertEqual(
            parse_transactions_csv._parse_transaction_amount("-£5.00"),
            Decimal("-5.00"),
        )

    def test_parses_valid_negative_price_with_currency_symbol_true_minus(self) -> None:
        self.assertEqual(
            parse_transactions_csv._parse_transaction_amount("−£5.00"),
            Decimal("-5.00"),
        )
        self.assertEqual(
            parse_transactions_csv._parse_transaction_amount("£−5.00"),
            Decimal("-5.00"),
        )

    def test_parses_valid_negative_price_without_currency_symbol(self) -> None:
        self.assertEqual(
            parse_transactions_csv._parse_transaction_amount("-5.00"),
            Decimal("-5.00"),
        )

    def test_parses_valid_negative_price_without_currency_symbol_true_minus(
        self,
    ) -> None:
        self.assertEqual(
            parse_transactions_csv._parse_transaction_amount("−5.00"),
            Decimal("-5.00"),
        )

    def test_raises_for_invalid_price_string(self) -> None:
        with self.assertRaises(InvalidOperation):
            parse_transactions_csv._parse_transaction_amount("5.0.0")


class TransactionRowTests(TestCase):
    valid_date = date(1997, 2, 27)
    valid_date_string = valid_date.strftime("%d/%m/%Y")
    valid_reference = "reference"
    valid_amount = Decimal("5.00")
    valid_amount_string = f"£{str(valid_amount)}"
    row_index = 123

    def test_from_row_raises_for_rows_of_incorrect_length(self) -> None:
        # row of length < 3
        too_short_row = ["foo", "bar"]
        with self.assertRaisesRegex(
            parse_transactions_csv.TransactionRowParsingError,
            f"row had {len(too_short_row)} items",
        ) as cm_too_short_row:
            parse_transactions_csv.TransactionRow.from_row(
                too_short_row,
                self.row_index,
            )
        for i in too_short_row:
            self.assertIn(i, str(cm_too_short_row.exception))
        # row of length > 3
        too_long_row = ["foo", "bar", "bish", "bash"]
        with self.assertRaisesRegex(
            parse_transactions_csv.TransactionRowParsingError,
            f"row had {len(too_long_row)} items",
        ) as cm_too_long_row:
            parse_transactions_csv.TransactionRow.from_row(
                too_long_row,
                self.row_index,
            )
        for i in too_long_row:
            self.assertIn(i, str(cm_too_long_row.exception))

    def test_from_row_raises_for_invalid_date(self) -> None:
        invalid_date = "2024-01-01"
        invalid_date_row = [
            invalid_date,
            self.valid_reference,
            self.valid_amount_string,
        ]
        with self.assertRaisesRegex(
            parse_transactions_csv.TransactionRowParsingError,
            invalid_date,
        ):
            parse_transactions_csv.TransactionRow.from_row(
                invalid_date_row,
                self.row_index,
            )

    def test_from_row_raises_for_invalid_amount(self) -> None:
        invalid_amount = "5.0.0"
        invalid_amount_row = [
            self.valid_date_string,
            self.valid_reference,
            invalid_amount,
        ]
        with self.assertRaisesRegex(
            parse_transactions_csv.TransactionRowParsingError,
            invalid_amount,
        ):
            parse_transactions_csv.TransactionRow.from_row(
                invalid_amount_row,
                self.row_index,
            )

    def test_from_row_successful_parsing(self) -> None:
        transaction_row = parse_transactions_csv.TransactionRow.from_row(
            [self.valid_date_string, self.valid_reference, self.valid_amount_string],
            self.row_index,
        )
        self.assertEqual(transaction_row.transaction_date, self.valid_date)
        self.assertEqual(transaction_row.reference, self.valid_reference)
        self.assertEqual(transaction_row.amount, self.valid_amount)
        self.assertEqual(transaction_row.row_index, self.row_index)


class TransactionsCsvTestCase(TestCase):
    transactions_file_path = pathlib.Path(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "..",
        "..",
        "transactions.csv",
    )

    def create_transactions_csv_file(self, content: list[list[str]]) -> None:
        self.delete_transactions_csv_file()
        with self.transactions_file_path.open("x") as f:
            csv_writer = csv.writer(f)
            csv_writer.writerows(content)

    def delete_transactions_csv_file(self) -> None:
        try:
            self.transactions_file_path.unlink(missing_ok=True)
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise

    def tearDown(self) -> None:
        self.delete_transactions_csv_file()


class CheckTransactionsFileTests(TransactionsCsvTestCase):

    def test_raises_when_file_missing(self) -> None:
        self.delete_transactions_csv_file()
        with self.assertRaisesRegex(
            parse_transactions_csv.TransactionsFileParsingError,
            f'no file named "{self.transactions_file_path.name}" in ',
        ):
            parse_transactions_csv._check_transactions_file(
                self.transactions_file_path.resolve()
            )

    def test_raises_when_header_row_incorrect(self) -> None:
        incorrect_headers = ["Foo", "Bar"]
        self.create_transactions_csv_file([incorrect_headers])
        with self.assertRaises(
            parse_transactions_csv.TransactionsFileParsingError
        ) as cm:
            parse_transactions_csv._check_transactions_file(self.transactions_file_path)
        thrown_exception = cm.exception
        for incorrect_header in incorrect_headers:
            self.assertIn(incorrect_header, str(thrown_exception))


class ParseTransactionsFileTests(TransactionsCsvTestCase):
    header_row = ["Date", "Reference", "Amount"]
    okay_row = ["27/02/1997", "reference", "£5.00"]

    def test_raises_informative_exception_for_row_of_incorrect_length(self) -> None:
        # arrange
        too_long_row = ["Foo", "Bar", "", ""]
        self.create_transactions_csv_file(
            [
                self.header_row,
                self.okay_row,
                too_long_row,
            ]
        )
        # act/assert
        with self.assertRaisesRegex(
            parse_transactions_csv.TransactionRowParsingError,
            f"Row 3 of transactions.csv was of length {len(too_long_row)}",
        ) as cm:
            parse_transactions_csv.parse_transactions_file()
        # verifying details row contents for the sake of easy identification
        too_long_row_summary = ", ".join(f'"{i}"' for i in too_long_row)
        self.assertIn(too_long_row_summary, str(cm.exception))

    def test_raises_informative_exception_for_date_parsing_error(self) -> None:
        # arrange
        malformed_date_row = ["2024-01-01", *self.okay_row[1:]]
        self.create_transactions_csv_file(
            [
                self.header_row,
                self.okay_row,
                self.okay_row,
                malformed_date_row,
            ]
        )
        # act/assert
        with self.assertRaises(parse_transactions_csv.TransactionRowParsingError) as cm:
            parse_transactions_csv.parse_transactions_file()
        self.assertIn(
            f"Error parsing row 4, column 1 of transactions.csv.",
            cm.exception.__notes__,
        )

    def test_raises_informative_exception_for_amount_parsing_error(self) -> None:
        # arrange
        malformed_amount_row = [*self.okay_row[:2], "5.0.0"]
        self.create_transactions_csv_file(
            [
                self.header_row,
                self.okay_row,
                malformed_amount_row,
            ]
        )
        # act/assert
        with self.assertRaises(parse_transactions_csv.TransactionRowParsingError) as cm:
            parse_transactions_csv.parse_transactions_file()
        self.assertIn(
            f"Error parsing row 3, column 3 of transactions.csv.",
            cm.exception.__notes__,
        )
