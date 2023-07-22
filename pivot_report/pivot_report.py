from myopt.nothing import Nothing
from pivot_report.pivot_field import DimensionField, MeasureField, PivotField
from pivot_report.pivot_table import PivotTable
from utils import checked_type, checked_list_type


class PivotReport:
    def __init__(
            self,
            row_fields: list[DimensionField],
            measure_fields: list[MeasureField],
            pivot_table: PivotTable
    ):
        self.row_fields: list[DimensionField] = checked_list_type(row_fields, DimensionField)
        self.measure_fields: list[MeasureField] = checked_list_type(measure_fields, MeasureField)
        self.fields: list[PivotField] = self.row_fields + self.measure_fields
        self.pivot_table: PivotTable = checked_type(pivot_table, PivotTable)
        for field in self.fields:
            assert field in pivot_table.fields, f"Field {field} not in {pivot_table.fields}"

    def headers(self) -> list[str]:
        return [field.name for field in self.fields]

    def as_table(self) -> list[list[any]]:
        print("Partitioning")
        partitioned_tables = [self.pivot_table]
        for field in self.row_fields:

            foo = [
                table
                for partitioned_table in partitioned_tables
                for table in partitioned_table.group_by(field).values()
            ]
            partitioned_tables = foo

        def dimensions(table: PivotTable):
            row = table.rows[0]
            return tuple(row.value(field) for field in self.row_fields)
        sorted_tables = sorted(
            partitioned_tables,
            key=dimensions
        )
        report_table = []
        last_dimension_row = [None for _ in self.row_fields]
        for table in sorted_tables:
            dimension_row = list(dimensions(table))
            display_row = [
                y.display_value if x is None or x != y else ""
                for x, y in zip(last_dimension_row, dimension_row)
            ]
            last_dimension_row = dimension_row
            measures = [measure_field.merge(table.values(measure_field)) for measure_field in self.measure_fields]
            report_row = display_row + measures
            report_table.append(report_row)
        return report_table


