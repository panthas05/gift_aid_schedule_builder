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

    # defaults for adding a row to the csv
    title = "Adml"
    first_name = "John"
    last_name = "Hext"

    house_number = "50"
    postcode = "SA18 3QJ"

    declaration_date = date(1993, 10, 8)
    declaration_date_string = declaration_date.strftime("%d/%m/%Y")

    _bool_to_string = lambda boolean: "1" if boolean else "0"

    valid_four_years_before_declaration = True
    valid_four_years_before_declaration_string = _bool_to_string(
        valid_four_years_before_declaration
    )

    valid_day_of_declaration = False
    valid_day_of_declaration_string = _bool_to_string(valid_day_of_declaration)

    valid_after_day_of_declaration = False
    valid_after_day_of_declaration_string = _bool_to_string(
        valid_after_day_of_declaration
    )

    identifier = "identifier"

    def _build_row(
        self,
        *,
        title: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        house_number_or_name: str | None = None,
        postcode: str | None = None,
        declaration_date_string: str | None = None,
        valid_four_years_before_declaration_string: str | None = None,
        valid_day_of_declaration_string: str | None = None,
        valid_after_day_of_declaration_string: str | None = None,
        identifier: str | None = None,
    ) -> list[str]:
        return [
            title if title is not None else self.title,
            first_name if first_name is not None else self.first_name,
            last_name if last_name is not None else self.last_name,
            (
                house_number_or_name
                if house_number_or_name is not None
                else self.house_number
            ),
            postcode if postcode is not None else self.postcode,
            (
                declaration_date_string
                if declaration_date_string is not None
                else self.declaration_date_string
            ),
            (
                valid_four_years_before_declaration_string
                if valid_four_years_before_declaration_string is not None
                else self.valid_four_years_before_declaration_string
            ),
            (
                valid_day_of_declaration_string
                if valid_day_of_declaration_string is not None
                else self.valid_day_of_declaration_string
            ),
            (
                valid_after_day_of_declaration_string
                if valid_after_day_of_declaration_string is not None
                else self.valid_after_day_of_declaration_string
            ),
            identifier if identifier is not None else self.identifier,
        ]

    def test_parsing(self) -> None:
        # arrange
        self.create_declarations_csv_file(
            [
                self.header_row,
                self._build_row(),
            ]
        )
        # act
        declarations = parse_declarations_csv.parse_declarations_file()
        # assert
        self.assertEqual(len(declarations), 1)
        declaration = declarations[0]
        for attribute, expected_value in [
            ("title", self.title),
            ("first_name", self.first_name),
            ("last_name", self.last_name),
            ("house_number_or_name", self.house_number),
            ("declaration_date", self.declaration_date),
            ("postcode", self.postcode),
            (
                "valid_four_years_before_declaration",
                self.valid_four_years_before_declaration,
            ),
            ("valid_day_of_declaration", self.valid_day_of_declaration),
            ("valid_after_day_of_declaration", self.valid_after_day_of_declaration),
            ("identifier", self.identifier),
        ]:
            self.assertEqual(
                getattr(declaration, attribute),
                expected_value,
                msg=f"Attribute was {attribute}",
            )

    def _check_locator_details(
        self,
        exception: parse_declarations_csv.DeclarationRowParsingError,
        column_number: int,
    ) -> None:
        note = exception.__notes__[0]
        self.assertIn("row 2", note)
        self.assertIn(f"column {column_number}", note)

    def test_raises_for_too_long_title(self) -> None:
        self.create_declarations_csv_file(
            [
                self.header_row,
                self._build_row(title="Most excellent flight lieutenant"),
            ]
        )
        with self.assertRaises(parse_declarations_csv.DeclarationRowParsingError) as cm:
            declarations = parse_declarations_csv.parse_declarations_file()

        exception = cm.exception
        self._check_locator_details(exception, 1)
        self.assertIn("Title should be no longer than four characters", str(exception))

    def test_raises_for_missing_first_name(self) -> None:
        self.create_declarations_csv_file(
            [
                self.header_row,
                self._build_row(first_name=""),
            ]
        )
        with self.assertRaises(parse_declarations_csv.DeclarationRowParsingError) as cm:
            declarations = parse_declarations_csv.parse_declarations_file()

        exception = cm.exception
        self._check_locator_details(exception, 2)
        self.assertIn("No first name provided.", str(exception))

    too_long_name = "supercalifragilisticexpialidociousfred"

    def test_raises_for_too_long_first_name(self) -> None:
        self.create_declarations_csv_file(
            [
                self.header_row,
                self._build_row(first_name=self.too_long_name),
            ]
        )
        with self.assertRaises(parse_declarations_csv.DeclarationRowParsingError) as cm:
            declarations = parse_declarations_csv.parse_declarations_file()

        exception = cm.exception
        self._check_locator_details(exception, 2)
        self.assertIn(self.too_long_name, str(exception))
        self.assertIn("longer than 35 characters", str(exception))

    def test_raises_for_missing_last_name(self) -> None:
        self.create_declarations_csv_file(
            [
                self.header_row,
                self._build_row(last_name=""),
            ]
        )
        with self.assertRaises(parse_declarations_csv.DeclarationRowParsingError) as cm:
            declarations = parse_declarations_csv.parse_declarations_file()

        exception = cm.exception
        self._check_locator_details(exception, 3)
        self.assertIn("No last name provided.", str(exception))

    def test_raises_for_too_long_last_name(self) -> None:
        self.create_declarations_csv_file(
            [
                self.header_row,
                self._build_row(last_name=self.too_long_name),
            ]
        )
        with self.assertRaises(parse_declarations_csv.DeclarationRowParsingError) as cm:
            declarations = parse_declarations_csv.parse_declarations_file()

        exception = cm.exception
        self._check_locator_details(exception, 3)
        self.assertIn(self.too_long_name, str(exception))
        self.assertIn("longer than 35 characters", str(exception))

    def test_raises_for_double_barrelled_last_name(self) -> None:
        double_barrelled_last_name = "foo-bar"
        self.create_declarations_csv_file(
            [
                self.header_row,
                self._build_row(last_name=double_barrelled_last_name),
            ]
        )
        with self.assertRaises(parse_declarations_csv.DeclarationRowParsingError) as cm:
            declarations = parse_declarations_csv.parse_declarations_file()

        exception = cm.exception
        self._check_locator_details(exception, 3)
        self.assertIn(double_barrelled_last_name, str(exception))
        self.assertIn("foo bar", str(exception))
        self.assertIn(
            "Double-barrelled last names should have a space instead of a hypen",
            str(exception),
        )

    def test_raises_for_too_long_house_name(self) -> None:
        too_long_house_name = "Buckingham Palace Buckingham Palace Buckingham Palace"
        self.create_declarations_csv_file(
            [
                self.header_row,
                self._build_row(house_number_or_name=too_long_house_name),
            ]
        )
        with self.assertRaises(parse_declarations_csv.DeclarationRowParsingError) as cm:
            declarations = parse_declarations_csv.parse_declarations_file()

        exception = cm.exception
        self._check_locator_details(exception, 4)
        self.assertIn(too_long_house_name, str(exception))
        self.assertIn(
            "longer than 40 characters",
            str(exception),
        )
