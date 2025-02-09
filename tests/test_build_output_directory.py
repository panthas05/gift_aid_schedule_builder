import build_output_directory
from logic.parsing import parse_transactions_csv
import models

from datetime import date
from decimal import Decimal
from unittest import TestCase


class DetermineWhetherTransactionGiftAidableForDeclarationTests(TestCase):
    declaration_date = date(2014, 9, 14)

    def setUp(self) -> None:
        super().setUp()
        # The values here are simply boilerplate
        self.transaction_row = parse_transactions_csv.TransactionRow(
            self.declaration_date,
            "FP: Reference",
            Decimal("5.00"),
            1,
        )
        self.declaration = models.DonorDeclaration(
            "Mr",
            "Foo",
            "Bar",
            "123",
            "B12 8QX",
            self.declaration_date,
            True,
            True,
            True,
            "reference",
        )

    def test_transaction_more_than_four_years_before_declaration(self) -> None:
        # arrange
        self.transaction_row.transaction_date = self.declaration_date.replace(
            year=self.declaration_date.year - 4,
            day=self.declaration_date.day - 1,
        )
        self.declaration.valid_four_years_before_declaration = True
        # act
        result = build_output_directory._determine_whether_transaction_gift_aidable_for_declaration(
            self.transaction_row, self.declaration
        )
        # assert
        self.assertEqual(
            result,
            build_output_directory.TransactionEligability.TRANSACTION_OCCURRED_MORE_THAN_FOUR_YEARS_BEFORE_DECLARATION,
        )

    def test_transaction_less_than_four_years_before_declaration_invalid(self) -> None:
        # arrange
        self.transaction_row.transaction_date = self.declaration_date.replace(
            year=self.declaration_date.year - 4,
        )
        self.declaration.valid_four_years_before_declaration = False
        # act
        result = build_output_directory._determine_whether_transaction_gift_aidable_for_declaration(
            self.transaction_row, self.declaration
        )
        # assert
        self.assertEqual(
            result,
            build_output_directory.TransactionEligability.DECLARATION_INVALID_FOUR_YEARS_PRECEEDING_DAY_OF_DECLARATION,
        )

    def test_transaction_less_than_four_years_before_declaration_valid(self) -> None:
        # arrange
        self.transaction_row.transaction_date = self.declaration_date.replace(
            year=self.declaration_date.year - 4,
        )
        self.declaration.valid_four_years_before_declaration = True
        # act
        result = build_output_directory._determine_whether_transaction_gift_aidable_for_declaration(
            self.transaction_row, self.declaration
        )
        # assert
        self.assertEqual(
            result, build_output_directory.TransactionEligability.IS_GIFT_AIDABLE
        )

    def test_transaction_day_of_declaration_invalid(self) -> None:
        # arrange
        self.transaction_row.transaction_date = self.declaration_date
        self.declaration.valid_day_of_declaration = False
        # act
        result = build_output_directory._determine_whether_transaction_gift_aidable_for_declaration(
            self.transaction_row, self.declaration
        )
        # assert
        self.assertEqual(
            result,
            build_output_directory.TransactionEligability.DECLARATION_INVALID_FOR_DAY_OF_DECLARATION,
        )

    def test_transaction_day_of_declaration_valid(self) -> None:
        # arrange
        self.transaction_row.transaction_date = self.declaration_date
        self.declaration.valid_day_of_declaration = True
        # act
        result = build_output_directory._determine_whether_transaction_gift_aidable_for_declaration(
            self.transaction_row, self.declaration
        )
        # assert
        self.assertEqual(
            result, build_output_directory.TransactionEligability.IS_GIFT_AIDABLE
        )

    def test_transaction_after_day_of_declaration_invalid(self) -> None:
        # arrange
        self.transaction_row.transaction_date = self.declaration_date.replace(
            day=self.declaration_date.day + 1
        )
        self.declaration.valid_after_day_of_declaration = False
        # act
        result = build_output_directory._determine_whether_transaction_gift_aidable_for_declaration(
            self.transaction_row, self.declaration
        )
        # assert
        self.assertEqual(
            result,
            build_output_directory.TransactionEligability.DECLARATION_INVALID_AFTER_DAY_OF_DECLARATION,
        )

    def test_transaction_after_day_of_declaration_valid(self) -> None:
        # arrange
        self.transaction_row.transaction_date = self.declaration_date.replace(
            day=self.declaration_date.day + 1
        )
        self.declaration.valid_after_day_of_declaration = True
        # act
        result = build_output_directory._determine_whether_transaction_gift_aidable_for_declaration(
            self.transaction_row, self.declaration
        )
        # assert
        self.assertEqual(
            result, build_output_directory.TransactionEligability.IS_GIFT_AIDABLE
        )
