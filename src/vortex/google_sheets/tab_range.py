from numbers import Number
from typing import Optional

from google_sheets import Tab
from utils import checked_type, checked_list_type


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


class TabCell:
    def __init__(self, tab: Tab, coordinates: CellCoordinates):
        self.tab: Tab = checked_type(tab, Tab)
        self.cell_coordinates: CellCoordinates = checked_type(coordinates, CellCoordinates)

    @property
    def in_a1_notation(self):
        return self.cell_coordinates.text

    @property
    def i_row(self) -> int:
        return self.cell_coordinates.i_row

    @property
    def i_col(self) -> int:
        return self.cell_coordinates.i_col

    def offset(self, num_rows: int = 0, num_cols: int = 0):
        return TabCell(
            tab=self.tab,
            coordinates=self.cell_coordinates.offset(num_rows=num_rows, num_cols=num_cols)
        )

    def column_letter(self):
        return CellCoordinates.column_text_from_index(self.i_col)


class Colors:
    BLACK = {
        "red": 0.0,
        "green": 0.0,
        "blue": 0.0,
    }


class TabRange:

    def __init__(self, top_left_cell: TabCell, num_rows: int, num_cols: int):
        self.top_left_cell: TabCell = checked_type(top_left_cell, TabCell)
        self.num_rows: int = checked_type(num_rows, int)
        self.num_cols: int = checked_type(num_cols, int)

    @property
    def tab(self):
        return self.top_left_cell.tab

    @property
    def in_a1_notation(self):
        t1 = self.top_left_cell.cell_coordinates
        if self.is_single_cell:
            return t1.text
        t2 = t1.offset(self.num_rows - 1, self.num_cols - 1)
        return f"{t1.text}:{t2.text}"

    @property
    def bottom_left_cell(self):
        return self.top_left_cell.offset(num_rows=self.num_rows - 1)

    @property
    def bottom_right_cell(self):
        return self.top_left_cell.offset(num_rows=self.num_rows - 1, num_cols=self.num_cols - 1)

    @staticmethod
    def from_range_name(tab: Tab, range_name: str):
        top_left, bottom_right = [CellCoordinates(text=text) for text in range_name.split(":")]
        return TabRange(
            top_left_cell=TabCell(tab, top_left),
            num_rows=bottom_right.i_row - top_left.i_row + 1,
            num_cols=bottom_right.i_col - top_left.i_col + 1,
        )

    @property
    def tab(self):
        return self.top_left_cell.tab

    @property
    def workbook(self):
        return self.tab.workbook

    def _service(self):
        return self.workbook._resource

    @property
    def as_json_range(self):
        return {
            "sheet_id": self.tab.tab_id,
            "start_row_index": self.top_left_cell.i_row,
            "start_column_index": self.top_left_cell.i_col,
            "end_row_index": self.top_left_cell.i_row + self.num_rows,
            "end_column_index": self.top_left_cell.i_col + self.num_cols,
        }

    @property
    def full_range_name(self):
        return f"{self.tab.tab_name}!{self.in_a1_notation}"

    def write_values(self, values: list[list[any]]):
        def to_excel(value):
            if isinstance(value, Number):
                return value
            else:
                return str(value)

        transformed_values = [
            [to_excel(value) for value in row]
            for row in values
        ]
        self._service().values().update(
            spreadsheetId=self.workbook.sheet_id,
            range=self.full_range_name,
            valueInputOption="USER_ENTERED",
            body={"values": transformed_values}

        ).execute()

    def background_colour_request(self, colour_json: str):
        return {
            "repeat_cell": {
                "range": self.as_json_range,
                "cell": {
                    "user_entered_format": {
                        "background_color": colour_json
                    }
                },
                "fields": "user_entered_format.background_color"
            }
        }

    def border_request(self, borders, style="SOLID", color=Colors.BLACK):
        checked_list_type(borders, str)

        border_style = {
            "style": style,
            "color": color
        }

        borders_description = {"range": self.as_json_range}
        for b in borders:
            borders_description[b] = border_style

        return {
            "update_borders": borders_description
        }

    def outline_border_request(self, style="SOLID_MEDIUM", color=Colors.BLACK):
        return self.border_request(borders=["top", "bottom", "left", "right"], style=style, color=color)

    def merge_columns_request(self):
        return {
            "merge_cells": {
                "merge_type": 'MERGE_ALL',
                "range": self.as_json_range
            }
        }

    def number_format_request(self, format: dict):
        return {
            "repeat_cell": {
                "range": self.as_json_range,
                "cell": {
                    "user_entered_format": {
                        "number_format": format
                    }
                },
                "fields": "user_entered_format.number_format"
            }
        }

    def set_decimal_format_request(self, format: str):
        return self.number_format_request({"type": "NUMBER", "pattern": format})

    def set_currency_format_request(self):
        return self.set_decimal_format_request("#,##0.00")

    def date_format_request(self, format: str):
        return self.number_format_request({"type": "DATE", "pattern": format})

    def percentage_format_request(self):
        return self.number_format_request({"type": "PERCENT", "pattern": "0.0%"})

    def user_entered_format_request(self, format):
        fields = ",".join([f"user_entered_format.{k}" for k in format.keys()])
        return {
            "repeat_cell": {
                "range": self.as_json_range,
                "cell": {
                    "user_entered_format": format
                },
                "fields": fields
            }
        }

    def horizontal_alignment_request(self, align: str):
        return self.user_entered_format_request({"horizontal_alignment": align})

    def center_text_request(self):
        return self.horizontal_alignment_request("CENTER")

    def right_align_text_request(self):
        return self.horizontal_alignment_request("right")

    def left_align_text_request(self):
        return self.horizontal_alignment_request("left")

    def text_format_request(self, format):
        return self.user_entered_format_request({"text_format": format})

    def set_bold_text_request(self):
        return self.text_format_request({"bold": True})

    @property
    def is_single_cell(self):
        return self.num_rows == 1 and self.num_cols == 1

    @property
    def as_single_cell(self):
        if not self.is_single_cell:
            raise ValueError(f"{self} is not a single cell")
        return self.top_left_cell

    @property
    def is_row(self):
        return self.num_rows == 1

    @property
    def is_column(self):
        return self.num_cols == 1

    @property
    def top_right_cell(self):
        return self[0, -1].top_left_cell

    @property
    def columns_in_a1_notation(self):
        return f"{self.top_left_cell.column_letter()}:{self.top_right_cell.column_letter()}"

    def __getitem__(self, indexish):
        if isinstance(indexish, (slice, int)):
            return self[indexish, :]
        checked_type(indexish, tuple)
        if len(indexish) != 2:
            raise ValueError("Expected tuple of length 2")
        row_slice, col_slice = indexish
        if isinstance(row_slice, int):
            if row_slice < 0:
                return self[self.num_rows + row_slice, col_slice]
            return self[row_slice:row_slice + 1, col_slice]
        if isinstance(row_slice, slice):
            if row_slice.start is None:
                return self[0: row_slice.stop, col_slice]
            if row_slice.start < 0:
                return self[self.num_rows + row_slice.start: row_slice.stop, col_slice]
            if row_slice.stop is None:
                return self[row_slice.start: self.num_rows, col_slice]
            if row_slice.stop < 0:
                return self[row_slice.start: row_slice.stop + self.num_rows, col_slice]

        if isinstance(col_slice, int):
            if col_slice < 0:
                return self[row_slice, self.num_cols + col_slice]
            return self[row_slice, col_slice: col_slice + 1]

        if isinstance(col_slice, slice):
            if col_slice.start is None:
                return self[row_slice, 0: col_slice.stop]
            if col_slice.start < 0:
                return self[row_slice, self.num_cols + col_slice.start: col_slice.stop]
            if col_slice.stop is None:
                return self[row_slice, col_slice.start: self.num_cols]
            if col_slice.stop < 0:
                return self[row_slice, col_slice.start: col_slice.stop + self.num_cols]

        def make_slice_absolute(_slice, N):
            new_start = 0 if _slice.start is None else _slice.start
            new_stop = N if _slice.stop is None else _slice.stop
            return slice(new_start, new_stop)

        row_slice = make_slice_absolute(row_slice, self.num_rows)
        col_slice = make_slice_absolute(col_slice, self.num_cols)
        new_top_left = self.top_left_cell.offset(row_slice.start, col_slice.start)
        num_rows = row_slice.stop - row_slice.start
        num_cols = col_slice.stop - col_slice.start
        return TabRange(new_top_left, num_rows, num_cols)

    @property
    def i_first_row(self):
        return self.top_left_cell.i_row

    @property
    def i_first_col(self):
        return self.top_left_cell.i_col

    @property
    def i_last_row(self):
        return self.i_first_row + self.num_rows - 1

    def offset(self, rows: int = 0, cols: int = 0) -> "TabRange":
        return TabRange(
            self.top_left_cell.offset(num_rows=rows, num_cols=cols),
            self.num_rows, self.num_cols
        )
