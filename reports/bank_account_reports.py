from collections import defaultdict

import tabulate

from env import ACCOUNT_MAPPING_TABLE, BANK_ACCOUNT_DATA
from pivot_report.pivot_field import DimensionField, MeasureField, PivotField, LEVEL_1, LEVEL_2, TIMS_DESCRIPTION, \
    TRANSACTION_VALUE, LEVEL_3, LEVEL_4, LEVEL_5
from pivot_report.pivot_report import PivotReport
from pivot_report.pivot_table import PivotRow, PivotTable
from reports.bank_account_pivot_values import bank_account_data_item_pivot_value
from tims_sheets.account_mapping_table import AccountMappingTable
from tims_sheets.bank_account_data import BankAccountData


class BankAccountReports:

    @staticmethod
    def pivot_report(
            bank_account_data: BankAccountData,
            row_fields: list[DimensionField],
            measure_fields: list[MeasureField]
    ) -> PivotReport:
        fields: list[PivotField] = row_fields + measure_fields
        rows = []
        for item in bank_account_data.items:
            rows.append(
                PivotRow(
                    {
                        field: bank_account_data_item_pivot_value(item, field)
                        for field in fields
                    }

                )
            )
        return PivotReport(row_fields, measure_fields, PivotTable(set(fields), rows))


if __name__ == '__main__':
    mapping_table = AccountMappingTable.from_spreadsheet(ACCOUNT_MAPPING_TABLE, force=True, clean=True)
    bank_account_data = BankAccountData.from_spreadsheet(BANK_ACCOUNT_DATA, mapping_table=None, force=False).with_mapping(mapping_table)

    report = BankAccountReports.pivot_report(
        bank_account_data=bank_account_data,
        row_fields=[LEVEL_1, LEVEL_2, LEVEL_3, LEVEL_4, LEVEL_5],
        measure_fields=[TRANSACTION_VALUE]
    )
    report.as_table()
    print(tabulate.tabulate(report.as_table(), headers=report.headers()))