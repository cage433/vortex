import tabulate

from date_range import Day
from date_range.month import Month
from env import ACCOUNT_MAPPING_TABLE, BANK_ACCOUNT_DATA
from pivot_report.pivot_field import DimensionField, MeasureField, PivotField, LEVEL_2, TRANSACTION_VALUE, LEVEL_3, DATE
from pivot_report.pivot_filter import PivotFilter
from pivot_report.pivot_report import PivotReport
from pivot_report.pivot_table import PivotRow, PivotTable
from reports.bank_account_pivot_values import bank_account_data_item_pivot_value
from tims_sheets.account_mapping_table import AccountMappingTable
from tims_sheets.bank_account_data import BankAccountData

__all__ = ["BankAccountReports"]

class BankAccountReports:

    @staticmethod
    def pivot_report(
            bank_account_data: BankAccountData,
            row_fields: list[DimensionField],
            measure_fields: list[MeasureField],
            extra_filter_fields: list[DimensionField],
            filters: list[PivotFilter],
    ) -> PivotReport:
        fields: list[PivotField] = row_fields + measure_fields
        rows = []
        for item in bank_account_data.items:
            report_row = PivotRow(
                {
                    field: bank_account_data_item_pivot_value(item, field)
                    for field in fields
                }
            )
            filter_row = PivotRow(
                {
                    field: bank_account_data_item_pivot_value(item, field)
                    for field in fields + extra_filter_fields
                }
            )
            if all(filter.include(filter_row) for filter in filters):
                rows.append(report_row)
        return PivotReport(row_fields, measure_fields, PivotTable(set(fields), rows))


if __name__ == '__main__':
    mapping_table = AccountMappingTable.from_spreadsheet(ACCOUNT_MAPPING_TABLE, force=True, clean=True)
    bank_account_data = BankAccountData \
        .from_spreadsheet(BANK_ACCOUNT_DATA, mapping_table=None, force=False) \
        .with_mapping(mapping_table) \
        .filter_by_date(first_day=Day(2019, 4, 1), last_day=Day(2020, 3, 31))

    report = BankAccountReports.pivot_report(
        bank_account_data=bank_account_data,
        row_fields=[LEVEL_2, LEVEL_3],
        measure_fields=[TRANSACTION_VALUE],
        extra_filter_fields=[DATE],
        filters=[PivotFilter.date_range_filter(DATE, Month(2020, 3))],
    )
    report.as_table()
    print(tabulate.tabulate(report.as_table(), headers=report.headers()))
