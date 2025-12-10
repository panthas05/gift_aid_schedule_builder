from logic.parsing import parse_declarations_csv

import csv
from datetime import date
import errno
import os
import pathlib
from unittest import TestCase


class CleanPostcodeTests(TestCase):

    def test_cleaning(self) -> None:
        self.assertEqual(
            parse_declarations_csv.clean_postcode("123ec1'?n8Q  \tx()"), "EC1N 8QX"
        )
        self.assertEqual(parse_declarations_csv.clean_postcode("x"), "X")


class ValidatePostcodeTests(TestCase):

    def test_passes_for_legitimate_UK_postcodes(self) -> None:
        self.assertTrue(parse_declarations_csv.validate_postcode("EC1N 8QX"))
        self.assertTrue(parse_declarations_csv.validate_postcode("SA18 3YF"))
        self.assertTrue(parse_declarations_csv.validate_postcode("W3 6LJ"))
        self.assertTrue(parse_declarations_csv.validate_postcode("B12 8QX"))

    def test_passes_for_international_postcodes(self) -> None:
        self.assertTrue(parse_declarations_csv.validate_postcode("X"))


class DeclarationsCsvTestCase(TestCase):
    declarations_file_path = pathlib.Path(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "..",
        "..",
        "declarations.csv",
    )
    # If there's already a file entitled "declarations.csv" in the project root
    # directory, relocate to "temp-declarations.csv", then move back to
    # "declarations.csv" after (so our tests don't go deleting the user's
    # files!) Speaking from painful experience :P
    declarations_temp_file_path = declarations_file_path.parent.joinpath(
        "temp-declarations.csv"
    )

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        if cls.declarations_file_path.exists():
            cls.declarations_file_path.rename(cls.declarations_temp_file_path)

    @classmethod
    def tearDownClass(cls) -> None:
        super().setUpClass()
        if cls.declarations_temp_file_path.exists():
            cls.declarations_temp_file_path.rename(cls.declarations_file_path)

    def create_declarations_csv_file(self, content: list[list[str]]) -> None:
        self.delete_declarations_csv_file()
        with self.declarations_file_path.open("x") as f:
            csv_writer = csv.writer(f)
            csv_writer.writerows(content)

    def delete_declarations_csv_file(self) -> None:
        try:
            self.declarations_file_path.unlink(missing_ok=True)
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise

    def tearDown(self) -> None:
        self.delete_declarations_csv_file()


class ParseDeclarationsCsvTests(DeclarationsCsvTestCase):
    header_row = [
        "Title",
        "First Name",
        "Last Name",
        "House Number or Name",
        "Postcode",
        "Date",
        "Valid Four Years Before Day of Declaration",
        "Valid Day of Declaration",
        "Valid After Day of Declaration",
        "Identifier",
    ]

    def test_parsing(self) -> None:
        # arrange
        title = "Rear Admiral"
        first_name = "John"
        last_name = "Hext"

        house_number = "50"
        postcode = "SA18 3QJ"

        declaration_date = date(1993, 10, 8)
        declaration_date_string = declaration_date.strftime("%d/%m/%Y")

        def bool_to_string(boolean: bool) -> str:
            return "1" if boolean else "0"

        valid_four_years_before_declaration = True
        valid_four_years_before_declaration_string = bool_to_string(
            valid_four_years_before_declaration
        )

        valid_day_of_declaration = False
        valid_day_of_declaration_string = bool_to_string(valid_day_of_declaration)

        valid_after_day_of_declaration = False
        valid_after_day_of_declaration_string = bool_to_string(
            valid_after_day_of_declaration
        )

        identifier = "identifier"

        row_under_test = [
            title,
            first_name,
            last_name,
            house_number,
            postcode,
            declaration_date_string,
            valid_four_years_before_declaration_string,
            valid_day_of_declaration_string,
            valid_after_day_of_declaration_string,
            identifier,
        ]
        self.create_declarations_csv_file(
            [
                self.header_row,
                row_under_test,
            ]
        )
        # act
        declarations = parse_declarations_csv.parse_declarations_file()
        # assert
        self.assertEqual(len(declarations), 1)
        declaration = declarations[0]
        for attribute, expected_value in [
            ("title", title),
            ("first_name", first_name),
            ("last_name", last_name),
            ("house_number_or_name", house_number),
            ("declaration_date", declaration_date),
            ("postcode", postcode),
            (
                "valid_four_years_before_declaration",
                valid_four_years_before_declaration,
            ),
            ("valid_day_of_declaration", valid_day_of_declaration),
            ("valid_after_day_of_declaration", valid_after_day_of_declaration),
            ("identifier", identifier),
        ]:
            self.assertEqual(
                getattr(declaration, attribute),
                expected_value,
                msg=f"Attribute was {attribute}",
            )
