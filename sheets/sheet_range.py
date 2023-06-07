from typing import Optional

from sheets import Worksheet
from utils import checked_type, checked_optional_type


class CellCoordinates:
    """
    Representation of an Excel cell, both using its text representation (e.g. "A1") and its zero offset
    row and column indices.

    The tricky part is converting the column representation, for example

            CBY -> 3 * 26 * 26 + 2 * 26 + 25  - 1

    where the final '- 1' is because we are zero offset.

    """

    def __init__(
            self,
            text: Optional[str] = None,
            i_row: Optional[int] = None,
            i_col: Optional[int] = None,
    ):
        if text is not None:
            self.text = checked_type(text, str)
        if i_row is not None:
            self.i_row = checked_type(i_row, int)
            self.i_col = checked_type(i_col, int)
        if text is None:
            self.text = self._text_from_row_and_col(self.i_row, self.i_col)
        if i_row is None:
            self.i_row, self.i_col = self._to_row_and_col(self.text)
        assert self.text == self._text_from_row_and_col(self.i_row, self.i_col), \
            f"Text '{self.text}' doesn't match row {self.i_row} and col {self.i_col}, {self._text_from_row_and_col(self.i_row, self.i_col)}"

    @staticmethod
    def column_text_from_index(i_col: int):
        col_text = ""
        # easier to work with the equivalent one offset column number
        col_1 = i_col + 1
        while col_1 >= 1:
            a = (col_1 - 1) % 26  # between 0 and 25
            col_text = chr(ord('A') + a) + col_text
            col_1 = (col_1 - a - 1) // 26
        return col_text

    @staticmethod
    def _text_from_row_and_col(row: int, col: int):
        return f"{CellCoordinates.column_text_from_index(col)}{row + 1}"

    @staticmethod
    def _to_row_and_col(coordinates: str):
        i_col = 0
        alpha_coords = [ord(c) - ord('A') for c in coordinates if c.isalpha()]
        for i, n in enumerate(reversed(alpha_coords)):
            i_col += (n + 1) * 26 ** i

        i_row = int(coordinates[len(alpha_coords):]) - 1
        return i_row, i_col - 1

    def __eq__(self, other):
        return isinstance(other, CellCoordinates) and self.text == other.text \
            and self.i_row == other.i_row and self.i_col == other.i_col

    def offset(self, num_rows: int = 0, num_cols: int = 0):
        return CellCoordinates(i_row=self.i_row + num_rows, i_col=self.i_col + num_cols)


class SheetCell:
    def __init__(self, worksheet: Worksheet, coordinates: CellCoordinates):
        self.worksheet: Worksheet = checked_type(worksheet, Worksheet)
        self.cell_coordinates: CellCoordinates = checked_type(coordinates, CellCoordinates)


class SheetRange:
    def __init__(self, top_left_cell: SheetCell, num_rows: Optional[int], num_cols: Optional[int]):
        self.top_left_cell: SheetCell = checked_type(top_left_cell, SheetCell)
        self.num_rows: Optional[int] = checked_optional_type(num_rows, int)
        self.num_cols: Optional[int] = checked_optional_type(num_cols, int)
        assert self.num_rows is not None or self.num_cols is not None, \
            "Must specify at least one of num_rows and num_cols"

    @property
    def range_name(self):
        t1 = self.top_left_cell.cell_coordinates
        if self.num_rows is None:
            return f"{t1.text}:{t1.i_col + self.num_cols}"
        elif self.num_cols is None:
            return f"{t1.text}:{CellCoordinates.column_text_from_index(t1.i_col + self.num_cols - 1)}"
        else:
            t2 = t1.offset(self.num_rows - 1, self.num_cols - 1)
            return f"{t1.text}:{t2.text}"

    @property
    def worksheet(self):
        return self.top_left_cell.worksheet

    @property
    def workbook(self):
        return self.worksheet.workbook

    def _service(self):
        return self.workbook._resource

    def write_values(self, values: list[list[any]]):
        full_range_name = f"{self.worksheet.sheet_name}!{self.range_name}"
        self._service().values().update(
            spreadsheetId=self.workbook.sheet_id,
            range=full_range_name,
            valueInputOption="USER_ENTERED",
            body={"values": values}

        ).execute()
