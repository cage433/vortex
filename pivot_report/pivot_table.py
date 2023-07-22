from pivot_report.pivot_field import PivotField
from pivot_report.pivot_value import PivotValue
from utils import checked_dict_type, checked_list_type
from utils.collection_utils import group_into_dict
from utils.type_checks import checked_set_type


class PivotRow:
    def __init__(self, values: dict[PivotField, PivotValue]):
        self.values: dict[PivotField, PivotValue] = checked_dict_type(values, PivotField, PivotValue)
        self.fields = values.keys()

    def value(self, field: PivotField) -> PivotValue:
        # assert field in self.fields, f"Field {field} not in {self.fields}"
        return self.values[field]


class PivotTable:
    def __init__(self, fields: set[PivotField], rows: list[PivotRow]):
        self.fields = checked_set_type(fields, PivotField)
        self.rows: list[PivotRow] = checked_list_type(rows, PivotRow)
        # for row in self.rows:
        #     assert row.values.keys() == fields, "All rows must have the same fields"

    def group_by(self, field: PivotField) -> dict[PivotValue, 'PivotTable']:
        grouped_rows = group_into_dict(self.rows, lambda row: row.value(field))
        return {value: PivotTable(self.fields, rows) for value, rows in grouped_rows.items()}

    def values(self, field: PivotField) -> list[PivotValue]:
        return [row.value(field) for row in self.rows]

    def __len__(self):
        return len(self.rows)


