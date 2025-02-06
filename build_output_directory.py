# gift_aid_schedule_builder, a script for building gift aid schedules for UK-based
# charities - Copyright (C) 2024  Peter Thomas

import models
from logic.parsing import parse_transactions_csv
import utils

from datetime import date
import enum
import os
import openpyxl
import pathlib
import re
import shutil
from typing import TextIO
import warnings

_output_file_name_regex = re.compile(r"output_\d{4}-\d{2}-\d{2}_\((\d+)\)")


def _determine_output_directory() -> pathlib.Path:
    outputs_directory = pathlib.Path(
        os.path.dirname(os.path.abspath(__file__)),
        "outputs",
    )
    outputs_directory.mkdir(exist_ok=True)

    date_stamp = date.today().isoformat()
    directory_base_name = f"output_{date_stamp}"

    existing_output_directories = [
        d.name
        for d in outputs_directory.iterdir()
        if d.name.startswith(directory_base_name)
    ]

    # does a directory exist that is called "output_YYYY-MM-DD"? if not we'll
    # use that name.
    initial_output_directory_exists = directory_base_name in existing_output_directories
    if not initial_output_directory_exists:
        return outputs_directory.joinpath(directory_base_name)

    # a directory exists that is called "output_YYYY-MM-DD", so append "_(n)" to
    # the name of the directory we'll use to indicate this is a subsequent run
    # from the same day. Determining the value of n:
    output_directories_numbers = [
        int(match.group(1))
        for fn in existing_output_directories
        if (match := _output_file_name_regex.match(fn))
    ]
    next_directory_number = (
        max(output_directories_numbers) + 1 if output_directories_numbers else 1
    )
    return outputs_directory.joinpath(
        f"{directory_base_name}_({next_directory_number})"
    )


_output_directory: pathlib.Path | None = None


def _get_output_directory() -> pathlib.Path:
    global _output_directory
    if _output_directory is None:
        _output_directory = _determine_output_directory()
        _output_directory.mkdir()
    return _output_directory


def _create_output_file() -> pathlib.Path:
    original_template_path = pathlib.Path("templates", "gift_aid_schedule__libre_.xlsx")
    output_directory = _get_output_directory()
    output_file_path = output_directory.joinpath("gift_aid_schedule__libre_.xlsx")
    shutil.copy(
        original_template_path,
        output_file_path,
    )
    return output_file_path


class MalformedXlsxError(Exception):
    pass


_earliest_donation_date_description_cell = "D12"
_earliest_donation_date_input_cell = "D13"

_expected_earliest_donation_date_description = (
    "Earliest donation date in the period of claim. (DD/MM/YY)"
)

_table_headers_cell_range = "B23:K23"
_expected_table_headers = [
    "Item",
    "Title",
    "First name",
    "Last name",
    "House name or number",
    "Postcode",
    "Aggregated donations",
    "Sponsored event",
    "Donation date",
    "Amount",
]
_first_table_row_index = 25


def _check_output_workbook(output_workbook: openpyxl.Workbook) -> None:
    if (worksheets_count := len(output_workbook.worksheets)) > 1:
        raise MalformedXlsxError(
            f"Expected there to be only one worksheet in the xlsx file - instead found "
            f"{worksheets_count}."
        )

    # interestingly the worksheet must have the name "R68GAD_V1_00_0_EN" -
    # validate this!
    main_worksheet = output_workbook.active
    if main_worksheet is None:
        raise MalformedXlsxError(
            "Workbook has no worksheets - expeced to find one with name "
            '"R68GAD_V1_00_0_EN".'
        )
    earliest_donation_date_description = main_worksheet[
        _earliest_donation_date_description_cell
    ].value
    if (
        earliest_donation_date_description
        != _expected_earliest_donation_date_description
    ):
        raise MalformedXlsxError(
            "Didn't find expected earliest donation date description in cell "
            f"{_earliest_donation_date_description_cell} (for earliest donation date "
            f"to be inserted into cell {_earliest_donation_date_input_cell}). Expected "
            f'to find "{_expected_earliest_donation_date_description}", instead got:'
            f'"{earliest_donation_date_description}".'
        )
    (table_headers_cells,) = main_worksheet[_table_headers_cell_range]
    table_headers = [c.value for c in table_headers_cells]
    if table_headers != _expected_table_headers:
        expected_table_headers_summary = ", ".join(
            f'"{th}"' for th in _expected_table_headers
        )
        table_headers_summary = ", ".join(f'"{th}"' for th in table_headers)
        raise MalformedXlsxError(
            "Didn't find expected table headers for transactions table, expected:\n"
            f"{expected_table_headers_summary}\nGot:\n{table_headers_summary}"
        )


class TransactionEligability(enum.Enum):
    IS_GIFT_AIDABLE = 1
    TRANSACTION_OCCURRED_MORE_THAN_FOUR_YEARS_BEFORE_DECLARATION = 2
    DECLARATION_INVALID_FOUR_YEARS_PRECEEDING_DAY_OF_DECLARATION = 3
    DECLARATION_INVALID_FOR_DAY_OF_DECLARATION = 4
    DECLARATION_INVALID_AFTER_DAY_OF_DECLARATION = 5


def _determine_whether_transaction_gift_aidable_for_declaration(
    transaction_row: parse_transactions_csv.TransactionRow,
    declaration: models.DonorDeclaration,
) -> TransactionEligability:
    transaction_date = transaction_row.transaction_date
    declaration_date = declaration.declaration_date

    four_years_preceeding_declaration_date = declaration_date.replace(
        year=declaration_date.year - 4
    )
    if transaction_date < four_years_preceeding_declaration_date:
        return (
            TransactionEligability.TRANSACTION_OCCURRED_MORE_THAN_FOUR_YEARS_BEFORE_DECLARATION
        )
    elif (
        four_years_preceeding_declaration_date <= transaction_date < declaration_date
        and not declaration.valid_four_years_before_declaration
    ):
        return (
            TransactionEligability.DECLARATION_INVALID_FOUR_YEARS_PRECEEDING_DAY_OF_DECLARATION
        )
    elif (
        transaction_date == declaration_date
        and not declaration.valid_day_of_declaration
    ):
        return TransactionEligability.DECLARATION_INVALID_FOR_DAY_OF_DECLARATION
    elif (
        transaction_date > declaration_date
        and not declaration.valid_after_day_of_declaration
    ):
        return TransactionEligability.DECLARATION_INVALID_AFTER_DAY_OF_DECLARATION
    else:
        return TransactionEligability.IS_GIFT_AIDABLE


def _log_non_gift_aidable_transaction_that_has_declaration(
    transactions_log_file: TextIO,
    log_prefix: str,
    transaction_row: parse_transactions_csv.TransactionRow,
    declaration: models.DonorDeclaration,
    transaction_gift_aidable_result: TransactionEligability,
) -> None:
    log_prefix = f"{log_prefix} had declaration from {declaration.donor_name}, however"
    if (
        transaction_gift_aidable_result
        == TransactionEligability.TRANSACTION_OCCURRED_MORE_THAN_FOUR_YEARS_BEFORE_DECLARATION
    ):
        transactions_log_file.write(
            f"{log_prefix} transaction occurred more than four years before "
            f"declaration date of {declaration.declaration_date.isoformat()}"
        )
    elif (
        transaction_gift_aidable_result
        == TransactionEligability.DECLARATION_INVALID_FOUR_YEARS_PRECEEDING_DAY_OF_DECLARATION
    ):
        transactions_log_file.write(
            f"{log_prefix} transaction occurred less than four years before "
            "declaration date, but declaration wasn't stated to cover donations made "
            "in the four years before it was signed (declaration date: "
            f"{declaration.declaration_date.isoformat()}, transaction date: "
            f"{transaction_row.transaction_date.isoformat()})"
        )
    elif (
        transaction_gift_aidable_result
        == TransactionEligability.DECLARATION_INVALID_FOR_DAY_OF_DECLARATION
    ):
        transactions_log_file.write(
            f"{log_prefix} transaction occurred on declaration date, but declaration "
            "wasn't stated to cover donations made on the day it was signed "
            f"(declaration/transaction date: {declaration.declaration_date.isoformat()})"
        )
    elif (
        transaction_gift_aidable_result
        == TransactionEligability.DECLARATION_INVALID_AFTER_DAY_OF_DECLARATION
    ):
        transactions_log_file.write(
            f"{log_prefix} transaction occurred after declaration date, but declaration "
            "wasn't stated to cover donations made after the day it was signed "
            f"(declaration date: {declaration.declaration_date.isoformat()}, "
            f"transaction date: {transaction_row.transaction_date.isoformat()})"
        )
    else:
        raise Exception(
            "Unexpected TransactionEligability passed to "
            "_log_non_gift_aidable_transaction_that_has_declaration: "
            f"{transaction_gift_aidable_result}"
        )


def _do_filtering_with_logging(
    transaction_rows: list[parse_transactions_csv.TransactionRow],
    declarations: list[models.DonorDeclaration],
    transactions_log_file: TextIO,
    transactions_that_need_manual_handling_log_file: TextIO,
) -> list[models.GiftAidableTransaction]:

    transactions: list[models.GiftAidableTransaction] = []
    for row_index, transaction_row in enumerate(transaction_rows, 2):
        log_prefix = f'Row {row_index}, reference "{transaction_row.reference}":'
        if transaction_row.amount is None:
            transactions_log_file.write(
                f"{log_prefix} skipping as transaction has no associated amount\n"
            )
            continue
        if transaction_row.amount < 0:
            transactions_log_file.write(
                f"{log_prefix} skipping as transaction amount is negative\n"
            )
            continue

        matching_declarations = [
            d for d in declarations if d.identifier in transaction_row.cleaned_reference
        ]
        if len(matching_declarations) == 0:
            transactions_log_file.write(
                f"{log_prefix} not detected as gift-aidable transaction\n"
            )
        elif len(matching_declarations) == 1:
            declaration = matching_declarations[0]

            transaction_eligability = (
                _determine_whether_transaction_gift_aidable_for_declaration(
                    transaction_row,
                    declaration,
                )
            )
            if transaction_eligability == TransactionEligability.IS_GIFT_AIDABLE:
                transactions_log_file.write(
                    f"{log_prefix} detected as gift-aidable transaction from "
                    f"{declaration.donor_name}\n"
                )
                transactions.append(
                    models.GiftAidableTransaction.from_transaction_row(
                        transaction_row,
                        declaration,
                    )
                )
            else:
                _log_non_gift_aidable_transaction_that_has_declaration(
                    transactions_log_file,
                    log_prefix,
                    transaction_row,
                    declaration,
                    transaction_eligability,
                )
        else:
            possible_donors_summary = ", ".join(
                d.donor_name for d in matching_declarations
            )
            transactions_log_file.write(
                f"{log_prefix} detected as gift-aidable transaction, but found "
                f"multiple possible donors: {possible_donors_summary}\n"
            )

            xlsx_row_index = _first_table_row_index + row_index - 2
            transactions_that_need_manual_handling_log_file.write(
                f"Transaction on row {xlsx_row_index} of xlsx schedule, from "
                f"row {row_index} of transactions.csv, possible donors were "
                f"{possible_donors_summary}\n"
            )
            transactions.append(
                models.GiftAidableTransaction.from_transaction_row(
                    transaction_row,
                    None,
                )
            )
        if len(transactions) == 1000:
            warnings.warn(
                "Over 1000 gift aidable transactions detected, but each schedule can "
                "only hold at most 1000 transactions - only processing up to row "
                f"{row_index} of transactions.csv. To process further transactions from "
                f"the file, delete rows 2-{row_index} of the file once this script has "
                "completed successfully, then rerun the script."
            )
            break
    return transactions


def _filter_gift_aidable_transactions(
    transaction_rows: list[parse_transactions_csv.TransactionRow],
    declarations: list[models.DonorDeclaration],
) -> list[models.GiftAidableTransaction]:
    output_directory = _get_output_directory()
    transactions_log_file_path = output_directory.joinpath("transactions_log.txt")
    transactions_that_need_manual_handling_log_file_path = output_directory.joinpath(
        "transactions_that_need_manual_handling.txt"
    )

    with transactions_log_file_path.open("x") as transactions_log_file:
        with transactions_that_need_manual_handling_log_file_path.open(
            "x"
        ) as transactions_that_need_manual_handling_log_file:
            gift_aidable_transactions = _do_filtering_with_logging(
                transaction_rows,
                declarations,
                transactions_log_file,
                transactions_that_need_manual_handling_log_file,
            )

    return gift_aidable_transactions


def _write_transactions_to_output_workbook(
    output_workbook: openpyxl.Workbook,
    gift_aidable_transactions: list[models.GiftAidableTransaction],
    output_file_path: pathlib.Path,
) -> None:
    if len(gift_aidable_transactions) == 0:
        return
    main_worksheet = output_workbook.active
    if main_worksheet is None:
        raise MalformedXlsxError(
            "Workbook has no worksheets - expeced to find one with name "
            '"R68GAD_V1_00_0_EN".'
        )

    # reporting earliest transaction date
    first_transaction_date = gift_aidable_transactions[0].transaction_date
    main_worksheet[_earliest_donation_date_input_cell].number_format = (
        openpyxl.styles.numbers.FORMAT_DATE_DDMMYY
    )
    main_worksheet[_earliest_donation_date_input_cell].value = first_transaction_date

    # writing rows
    for row_index, transaction in enumerate(
        gift_aidable_transactions,
        _first_table_row_index,
    ):
        declaration = transaction.donor_declaration
        if declaration:
            main_worksheet[f"C{row_index}"].value = declaration.title
            main_worksheet[f"D{row_index}"].value = declaration.first_name
            main_worksheet[f"E{row_index}"].value = declaration.last_name
            main_worksheet[f"F{row_index}"].value = declaration.house_name_or_number
            main_worksheet[f"G{row_index}"].value = declaration.postcode

        main_worksheet[f"J{row_index}"].number_format = (
            openpyxl.styles.numbers.FORMAT_DATE_DDMMYY
        )
        main_worksheet[f"J{row_index}"].value = transaction.transaction_date

        main_worksheet[f"K{row_index}"].value = transaction.amount
        main_worksheet[f"K{row_index}"].number_format = "#,##0.00"
    output_workbook.save(output_file_path.resolve())


def build_output_directory(
    transaction_rows: list[parse_transactions_csv.TransactionRow],
    declarations: list[models.DonorDeclaration],
) -> None:
    utils.clear_then_overwrite_print("Building and checking output file...")
    output_file_path = _create_output_file()

    output_workbook = openpyxl.load_workbook(
        output_file_path.resolve(),
        keep_vba=True,
        rich_text=True,
    )
    _check_output_workbook(output_workbook)
    utils.clear_then_overwrite_print("Output file built")

    utils.clear_then_overwrite_print(
        "Finding gift-aidable transactions in transactions.csv..."
    )
    gift_aidable_transactions = _filter_gift_aidable_transactions(
        transaction_rows,
        declarations,
    )
    utils.clear_then_overwrite_print(
        "Writing gift-aidable transactions to output file..."
    )
    _write_transactions_to_output_workbook(
        output_workbook,
        gift_aidable_transactions,
        output_file_path,
    )
    utils.clear_then_overwrite_print("Output file written")

    # finally, copying in transactions csv and declarations csv for ease of
    # auditability/reviewing what the script did
    utils.clear_then_overwrite_print("Copying ancillary files to output directory")
    output_directory = _get_output_directory()
    for file_name in ["transactions.csv", "declarations.csv"]:
        shutil.copy(
            pathlib.Path(
                os.path.dirname(os.path.abspath(__file__)),
                file_name,
            ),
            output_directory.joinpath(file_name),
        )

    # clearing whatever was last written to the terminal
    utils.clear_then_overwrite_print("")
    output_directory_files = [
        "A completed gift aid schedule (gift_aid_schedule__libre_.xlsx)",
        "A list of transactions that may be gift aidable, but require attention (transactions_that_need_manual_handling.txt)",
        "A log, detailing what was done with each row of transactions.csv (transactions_log.txt)",
        "A copy of transactions.csv",
        "A copy of declarations.csv",
    ]
    output_directory_files_summary = "".join(
        f"\n\t- {odf}" for odf in output_directory_files
    )
    print(
        f"Done. Files written to:\n{output_directory.absolute()}\nPlease find within "
        f"that folder:{output_directory_files_summary}\nAfter you've checked that the "
        "schedule looks okay, and resolved any transactions listed in "
        "transactions_that_need_manual_handling.txt, you can upload the schedule to "
        "make a gift aid claim here: https://www.gov.uk/claim-gift-aid-online"
    )
