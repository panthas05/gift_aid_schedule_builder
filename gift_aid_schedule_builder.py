# gift_aid_schedule_builder, a script for building gift aid schedules for UK-based
# charities - Copyright (C) 2024  Peter Thomas

import build_output_directory
from logic.parsing import parse_transactions_csv, parse_declarations_csv
import models


def main() -> None:
    # TODO: extend to take a flag, which specifies either "excel" or "libre", and uses
    # the corresponding spreadsheet when generating the output.
    transaction_rows = parse_transactions_csv.parse_transactions_file()
    declarations = [
        models.DonorDeclaration.from_declaration_row(dr)
        for dr in parse_declarations_csv.parse_declarations_file()
    ]
    build_output_directory.build_output_directory(
        transaction_rows,
        declarations,
    )


if __name__ == "__main__":
    main()
