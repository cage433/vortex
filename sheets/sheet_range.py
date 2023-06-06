from typing import Optional

from sheets import Worksheet
from utils import checked_type, checked_optional_type


class CellCoordinates:
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
    def _text_from_row_and_col(row: int, col: int):
        # one offset
        # rep = [[1, 26], 26 * [1, 26], 26 * 26 * [1, 26]]
        col_1 = col + 1
        col_text = ""
        # col //= 26
        while col_1 >= 1:
            a = (col_1 - 1) % 26  # between 0 and 25
            col_text = chr(ord('A') + a) + col_text
            col_1 = (col_1 - a - 1) // 26

        #
        # col_text = chr(ord('A') + col % 26)
        # col //= 26
        # col -= 1
        # while col > 0:
        #     col_text = chr(ord('A') + col % 26) + col_text
        #     col //= 26
        #     col -= 1
        return f"{col_text}{row + 1}"

    @staticmethod
    def _to_row_and_col(coordinates: str):
        i_col = 0
        alpha_coords = [ord(c) - ord('A') for c in coordinates if c.isalpha()]
        for i, n in enumerate(reversed(alpha_coords)):
            i_col += (n + 1) * 26 ** i

        i_row = int(coordinates[len(alpha_coords):]) - 1
        return i_row, i_col - 1

    def __eq__(self, other):
        return isinstance(other, CellCoordinates) and self.text == other.text


class SheetCell:
    def __init__(self, worksheet: Worksheet, coordinates: CellCoordinates):
        self.worksheet: Worksheet = checked_type(worksheet, Worksheet)
        self.cell_coordinates: CellCoordinates = checked_type(coordinates, CellCoordinates)


class SheetRange:
    def __init(self, worksheet: Worksheet, top_left_cell: SheetCell, num_rows: Optional[int], num_cols: Optional[int]):
        self.worksheet: Worksheet = checked_type(worksheet, Worksheet)
        self.top_left_cell: SheetCell = checked_type(top_left_cell, SheetCell)
        self.num_rows: Optional[int] = checked_optional_type(num_rows, int)
        self.num_cols: Optional[int] = checked_optional_type(num_cols, int)
