from logic import key_cleaning
from logic.parsing import parse_declarations_csv, parse_transactions_csv

from datetime import date
from decimal import Decimal
import enum


class DonorDeclaration:

    def __init__(
        self,
        title: str,
        first_name: str,
        last_name: str,
        house_name_or_number: str,
        postcode: str,
        declaration_date: date,
        valid_four_years_before_declaration: bool,
        valid_day_of_declaration: bool,
        valid_after_day_of_declaration: bool,
        identifier: str,
    ) -> None:
        self.title = title
        self.first_name = first_name
        self.last_name = last_name
        self.house_name_or_number = house_name_or_number
        self.postcode = postcode

        self.declaration_date = declaration_date
        self.valid_four_years_before_declaration = valid_four_years_before_declaration
        self.valid_day_of_declaration = valid_day_of_declaration
        self.valid_after_day_of_declaration = valid_after_day_of_declaration

        self.identifier = identifier

    @property
    def donor_name(self) -> str:
        return " ".join(i for i in [self.title, self.first_name, self.last_name] if i)

    @classmethod
    def from_declaration_row(
        cls,
        declaration_row: parse_declarations_csv.DeclarationRow,
    ) -> "DonorDeclaration":
        return cls(
            declaration_row.title,
            declaration_row.first_name,
            declaration_row.last_name,
            declaration_row.house_number_or_name,
            declaration_row.postcode,
            declaration_row.declaration_date,
            declaration_row.valid_four_years_before_declaration,
            declaration_row.valid_day_of_declaration,
            declaration_row.valid_after_day_of_declaration,
            key_cleaning.clean_key(declaration_row.identifier),
        )


class GiftAidableTransaction:

    def __init__(
        self,
        transaction_date: date,
        amount: Decimal,
        donor_declaration: DonorDeclaration | None,
    ) -> None:
        self.transaction_date = transaction_date
        self.amount = amount
        self.donor_declaration = donor_declaration

    @classmethod
    def from_transaction_row(
        cls,
        transaction_row: parse_transactions_csv.TransactionRow,
        donor_declaration: DonorDeclaration | None,
    ) -> "GiftAidableTransaction":
        if transaction_row.amount is None or transaction_row.amount < 0:
            raise ValueError(
                "Can only build a GiftAidableTransaction instance from a TransactionRow instance "
                "with an amount that is greater than zero."
            )
        return cls(
            transaction_row.transaction_date,
            transaction_row.amount,
            donor_declaration,
        )
