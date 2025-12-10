import csv
import os
import pathlib
import re
from datetime import date

import utils

from . import dates, row_parsing_exception


class DeclarationRowParsingError(row_parsing_exception.RowParsingError):
    pass


_invalid_amount_characters_regex = re.compile(r"[^\d\.]")


class BooleanParsingError(Exception):
    pass


def _parse_boolean(boolean_string: str) -> bool:
    if boolean_string == "0":
        return False
    elif boolean_string == "1":
        return True
    else:
        raise BooleanParsingError(
            'Expected a boolean value to be represented by either a "0" or a "1", got '
            f'"{boolean_string}"'
        )


def clean_postcode(postcode: str) -> str:
    # map to upper case
    postcode = postcode.upper().strip()
    if postcode == "X":
        # non-UK resident donors
        return postcode
    # remove non-alphabetical characters from start
    postcode = re.sub(r"^[^A-Z]+", "", postcode)
    # remove non-alphabetical characters from end
    postcode = re.sub(r"[^A-Z]+$", "", postcode)
    # remove any other gunk which made its way in
    postcode = re.sub(r"[^A-Z\d]", "", postcode)
    # insert the space into the correct location
    if len(postcode) > 2:
        postcode = f"{postcode[:-3]} {postcode[-3:]}"
    return postcode


# I assume you're not receiving donations from girobank :P
valid_uk_postcode_regex = re.compile(r"^[A-Z]{1,2}\d{1,2}[A-Z]? \d[A-Z]{2}$")


def validate_postcode(cleaned_postcode: str) -> bool:
    """
    Return value indicates if valid UK postcode, True meaning valid, False
    meaning invalid.
    """
    if cleaned_postcode == "X":
        return True
    return bool(valid_uk_postcode_regex.match(cleaned_postcode))


class DeclarationRow:
    def __init__(
        self,
        title: str,
        first_name: str,
        last_name: str,
        house_number_or_name: str,
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

        self.house_number_or_name = house_number_or_name
        self.postcode = postcode

        self.declaration_date = declaration_date

        self.valid_four_years_before_declaration = valid_four_years_before_declaration
        self.valid_day_of_declaration = valid_day_of_declaration
        self.valid_after_day_of_declaration = valid_after_day_of_declaration
        self.identifier = identifier

    @classmethod
    def from_row(
        cls,
        row: list[str],
    ) -> "DeclarationRow":
        if not (row_length := len(row)) == 10:
            raise DeclarationRowParsingError(
                None,
                "Expected each declaration to be represented by a row with ten "
                f"items - row had {row_length} items.",
            )
        # parsing data
        [
            title,
            first_name,
            last_name,
            house_number_or_name,
            postcode,
        ] = [
            row[0].strip(),
            row[1].strip(),
            row[2].strip(),
            row[3].strip(),
            clean_postcode(row[4]),
        ]

        if len(title) > 4:
            raise DeclarationRowParsingError(
                1, "Title should be no longer than four characters"
            )
        if first_name == "":
            raise DeclarationRowParsingError(2, "No first name provided.")
        if len(first_name) > 35:
            raise DeclarationRowParsingError(
                2,
                f'The first name "{first_name}" is longer than 35 characters - '
                "please shorten it to being within the 35 character limit.",
            )
        if last_name == "":
            raise DeclarationRowParsingError(3, "No last name provided.")
        if len(last_name) > 35:
            raise DeclarationRowParsingError(
                3,
                f'The last name "{last_name}" is longer than 35 characters - '
                "please shorten it to being within the 35 character limit.",
            )
        if "-" in last_name:
            cleaned_last_name = last_name.replace("-", " ")
            raise DeclarationRowParsingError(
                3,
                "Double-barrelled last names should have a space instead of a hypen. "
                f'Consider using "{cleaned_last_name}" instead of "{last_name}".',
            )

        if house_number_or_name == "":
            raise DeclarationRowParsingError(4, "No house number (or name) provided.")
        if len(house_number_or_name) > 40:
            raise DeclarationRowParsingError(
                4,
                f'The house name "{house_number_or_name}" is longer than 40 '
                "characters - please shorten it to being within the 40 character "
                "limit.",
            )
        if postcode == "":
            raise DeclarationRowParsingError(5, "No postcode provided.")
        if not validate_postcode(postcode):
            raise DeclarationRowParsingError(5, f"Invalid postcode: {row[4]}.")

        try:
            declaration_date = dates.parse_uk_formatted_date(row[5].strip())
        except ValueError:
            raise DeclarationRowParsingError(
                6,
                f'Error parsing date "{row[5]}", expected date of the form dd/mm/yyyy '
                "or dd/mm/yy.",
            )

        try:
            valid_four_years_before_declaration = _parse_boolean(row[6].strip())
        except BooleanParsingError:
            raise DeclarationRowParsingError(
                7,
                'Error parsing "Valid Four Years Before Day of Declaration" value, was '
                'expecting either "1" if the declaration covers the four years '
                'preceeding the date the declaration was signed or "0" if it doesn\'t, '
                f'instead got "{row[6]}"',
            )

        try:
            valid_day_of_declaration = _parse_boolean(row[7].strip())
        except BooleanParsingError:
            raise DeclarationRowParsingError(
                8,
                'Error parsing "Valid Day of Declaration" value, was expecting either '
                '"1" if the declaration covers the date the declaration was signed '
                f'or "0" if it doesn\'t, instead got "{row[7]}"',
            )

        try:
            valid_after_day_of_declaration = _parse_boolean(row[8].strip())
        except BooleanParsingError:
            raise DeclarationRowParsingError(
                9,
                'Error parsing "Valid After Day of Declaration" value, was expecting '
                'either "1" if the declaration is valid for days following the date '
                f'the declaration was signed or "0" if it isn\'t, instead got "{row[8]}"',
            )

        identifier = row[9].strip()
        if identifier == "":
            raise DeclarationRowParsingError(
                10,
                "No identifier provided - please consult the README for information "
                "about the value you need to provide in this column.",
            )

        return cls(
            title,
            first_name,
            last_name,
            house_number_or_name,
            postcode,
            declaration_date,
            valid_four_years_before_declaration,
            valid_day_of_declaration,
            valid_after_day_of_declaration,
            identifier,
        )


class DeclarationsFileParsingError(Exception):
    pass


def _verify_file_exists(declarations_file_path: pathlib.Path) -> None:
    if not declarations_file_path.is_file():
        raise DeclarationsFileParsingError(
            f'There is no file named "{declarations_file_path.name}" in '
            f"{declarations_file_path.parent}."
        )


def _check_header_row(header_row: list[str]) -> None:
    should_raise = len(header_row) != 10

    expected_header_row = [
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
    if not should_raise:
        cleaned_header_row = [h.strip().lower() for h in header_row]
        cleaned_expected_header_row = [h.lower() for h in expected_header_row]
        should_raise = cleaned_header_row != cleaned_expected_header_row

    if should_raise:
        csv_headers_summary = ", ".join(f'"{h}"' for h in header_row)
        expected_headers_summary = ", ".join(f'"{h}' for h in expected_header_row)
        raise DeclarationsFileParsingError(
            f"Expected declarations csv to have three columns with headers "
            f"{expected_headers_summary}, instead got headers {csv_headers_summary}"
        )


def _check_declarations_file(declarations_file_path: pathlib.Path) -> None:
    _verify_file_exists(declarations_file_path)
    with declarations_file_path.open() as declarations_file:
        header_row = declarations_file.readline().strip().split(",")
    _check_header_row(header_row)


def parse_declarations_file() -> list[DeclarationRow]:
    # look for declarations file in project directory
    declarations_file_path = pathlib.Path(
        os.path.dirname(os.path.realpath(__file__)),
        "..",
        "..",
        "declarations.csv",
    )
    utils.clear_then_overwrite_print("Checking declarations file...")
    _check_declarations_file(declarations_file_path)
    utils.clear_then_overwrite_print("Declarations file passed checks")
    # parsing file contents
    utils.clear_then_overwrite_print("Parsing declarations file...")
    declarations: list[DeclarationRow] = []
    with declarations_file_path.open() as declarations_file:
        declarations_reader = csv.reader(declarations_file)
        # skip header row
        _ = next(declarations_reader)

        for row_index, row in enumerate(declarations_reader, 2):
            if (row_length := len(row)) != 10:
                row_contents = ", ".join(f'"{i}"' for i in row)
                raise DeclarationRowParsingError(
                    None,
                    f"Row {row_index} of {declarations_file_path.name} was of length "
                    f"{row_length} - rows should be of length 10, holding the columns "
                    'specified in "declarations.csv", which can be found in the '
                    '"templates" folder/directory. Instead, the row contained: '
                    f"{row_contents}",
                )

            try:
                declarations.append(DeclarationRow.from_row(row))
            except DeclarationRowParsingError as e:
                e.add_note(
                    f"Error parsing row {row_index}, column {e.column_number} of "
                    "declarations.csv."
                )
                raise e

    utils.clear_then_overwrite_print("Declarations file parsed...")
    return declarations
