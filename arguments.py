import enum
import re
from typing import Any


class NoSpreadsheetTypeProvided(Exception):
    pass


class UnexpectedSpreadsheetType(Exception):
    def __init__(self, *args: Any, passed_value: str) -> None:
        super().__init__(*args)
        self.passed_value = passed_value


class SpreadsheetType(enum.Enum):
    EXCEL = "excel"
    LIBRE = "libre"


def _parse_spreadsheet_type(spreadsheet_type_str: str) -> SpreadsheetType:
    if spreadsheet_type_str == "excel":
        return SpreadsheetType.EXCEL
    elif spreadsheet_type_str == "libre":
        return SpreadsheetType.LIBRE
    else:
        raise UnexpectedSpreadsheetType(passed_value=spreadsheet_type_str)


_spreadsheet_type_argument_regex = re.compile(r"--output=(\w+)")


def parse_arguments(arguments: list[str]) -> SpreadsheetType:
    spreadsheet_type: SpreadsheetType | None = None
    for argument in arguments:
        if match := _spreadsheet_type_argument_regex.match(argument):
            return _parse_spreadsheet_type(match.group(1))

    raise NoSpreadsheetTypeProvided()
