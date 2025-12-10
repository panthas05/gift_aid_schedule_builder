from typing import Any


class RowParsingError(Exception):

    def __init__(
        self,
        column_number: int | None,
        *args: Any,
    ) -> None:
        super().__init__(*args)
        self.column_number = column_number
