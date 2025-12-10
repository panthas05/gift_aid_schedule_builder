# gift_aid_schedule_builder, a script for building gift aid schedules for UK-based
# charities - Copyright (C) 2024  Peter Thomas

from . import dates, row_parsing_exception
from logic import key_cleaning
import utils

import csv
from datetime import date
from decimal import Decimal, InvalidOperation
import pathlib
import os
import re
import sys
from typing import Any


class TransactionRowParsingError(row_parsing_exception.RowParsingError):
    pass


_invalid_amount_characters_regex = re.compile(r"[^\d\-\.]")


def _clean_amount_string(amount_string: str) -> str:
    # removing any usage of "true minus"
    amount_string = amount_string.replace("−", "-")
    return _invalid_amount_characters_regex.sub("", amount_string)


def _parse_transaction_amount(amount_string: str) -> Decimal | None:
    cleaned_amount_string = _clean_amount_string(amount_string)
    # Some statements represent value-less transactions as e.g. "--"
    if not re.search(r"\d", cleaned_amount_string):
        return None
    return Decimal(cleaned_amount_string)


class TransactionRow:

    def __init__(
        self,
        transaction_date: date,
        reference: str,
        amount: Decimal | None,
        row_index: int,
    ) -> None:
        self.reference = reference
        self.amount = amount
        self.transaction_date = transaction_date
        self.row_index = row_index

    @property
    def cleaned_reference(self) -> str:
        return key_cleaning.clean_key(self.reference)

    @classmethod
    def from_row(
        cls,
        row: list[str],
        row_index: int,
    ) -> "TransactionRow":
        if not len(row) == 3:
            row_summary = ", ".join(f'"{i}"' for i in row)
            raise TransactionRowParsingError(
                None,
                "Expected each transaction to be represented by a row with three "
                f"items - row had {len(row)} items: {row_summary}.",
            )
        # parsing data
        try:
            transaction_date = dates.parse_uk_formatted_date(row[0].strip())
        except ValueError:
            raise TransactionRowParsingError(
                1,
                f'Error parsing date "{row[0]}", expected date of the form dd/mm/yyyy '
                "or dd/mm/yy.",
            )
        reference = row[1]
        try:
            amount = _parse_transaction_amount(row[2])
        except InvalidOperation:
            raise TransactionRowParsingError(
                3, f'Error parsing amount "{row[2]}" to Decimal.'
            )
        return cls(
            transaction_date,
            reference,
            amount,
            row_index,
        )


class TransactionsFileParsingError(Exception):
    pass


def _verify_file_exists(transactions_file_path: pathlib.Path) -> None:
    if not transactions_file_path.is_file():
        raise TransactionsFileParsingError(
            f'There is no file named "{transactions_file_path.name}" in '
            f"{transactions_file_path.parent}."
        )


def _check_header_row(header_row: list[str]) -> None:
    should_raise = len(header_row) != 3

    if not should_raise:
        cleaned_header_row = [h.strip().lower() for h in header_row[:3]]
        expected_header_row = ["date", "reference", "amount"]
        should_raise = cleaned_header_row != expected_header_row

    if should_raise:
        csv_headers_summary = ", ".join(f'"{h}"' for h in header_row)
        raise TransactionsFileParsingError(
            'Expected transactions csv to have three columns with headers "Date", '
            f'"Reference", and "Amount", instead got headers {csv_headers_summary}'
        )


def _check_transactions_file(transactions_file_path: pathlib.Path) -> None:
    _verify_file_exists(transactions_file_path)
    with transactions_file_path.open() as transactions_file:
        header_row = transactions_file.readline().strip().split(",")
    _check_header_row(header_row)


def parse_transactions_file() -> list[TransactionRow]:
    # look for transactions file in project directory
    transactions_file_path = pathlib.Path(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "..",
        "transactions.csv",
    )
    utils.clear_then_overwrite_print("Checking transactions file...")
    _check_transactions_file(transactions_file_path)
    utils.clear_then_overwrite_print("Transactions file passed checks")
    # parsing file contents
    utils.clear_then_overwrite_print("Parsing transactions file...")
    transactions: list[TransactionRow] = []
    with transactions_file_path.open() as transactions_file:
        transactions_reader = csv.reader(transactions_file)
        # skip header row
        _header_row = next(transactions_reader)

        for row_index, row in enumerate(transactions_reader, 2):
            if (row_length := len(row)) != 3:
                row_contents = ", ".join(f'"{i}"' for i in row)
                raise TransactionRowParsingError(
                    None,
                    f"Row {row_index} of {transactions_file_path.name} was of length "
                    f"{row_length} - rows should be of length 3, holding a date, a "
                    "reference, and an amount for the transaction they represent. Row "
                    f"contents was: {row_contents}",
                )

            try:
                transactions.append(
                    TransactionRow.from_row(
                        row,
                        row_index,
                    )
                )
            except TransactionRowParsingError as e:
                e.add_note(
                    f"Error parsing row {row_index}, column {e.column_number} of "
                    f"{transactions_file_path.name}."
                )
                raise e
    utils.clear_then_overwrite_print("Transactions file parsed...")

    return transactions
