# gift_aid_schedule_builder, a script for building gift aid schedules for UK-based
# charities - Copyright (C) 2024  Peter Thomas

import build_output_directory
from logic.parsing import parse_transactions_csv, parse_declarations_csv
import models
import arguments
import sys


def main(spreadsheet_type: arguments.SpreadsheetType) -> None:
    transaction_rows = parse_transactions_csv.parse_transactions_file()
    declarations = [
        models.DonorDeclaration.from_declaration_row(dr)
        for dr in parse_declarations_csv.parse_declarations_file()
    ]
    build_output_directory.build_output_directory(
        transaction_rows,
        declarations,
        spreadsheet_type,
    )


if __name__ == "__main__":
    try:
        spreadsheet_type = arguments.parse_arguments(sys.argv)
        main(spreadsheet_type)
    except arguments.NoSpreadsheetTypeProvided:
        print(
            "Please specify the type of spreadsheet you wish to be output "
            "(hint: use --output=excel if you use excel or --output=libre if "
            "you use libreoffice)."
        )
    except arguments.UnexpectedSpreadsheetType as e:
        print(
            f'Unexpected spreadsheet type "{e.passed_value}", expected either '
            '"excel" or "libre".'
        )
