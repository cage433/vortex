import tabulate

from date_range import Day
from date_range.month import Month
from env import BANK_ACCOUNT_DATA, ACCOUNT_MAPPING_TABLE
from myopt.something import Something
from pivot_report.pivot_field import LEVEL_2, LEVEL_3, TRANSACTION_VALUE, DATE, LEVEL_4
from pivot_report.pivot_filter import PivotFilter
from pivot_report.pivot_value import StringPivotValue, OptionalStringPivotValue
from reports.bank_account_reports import BankAccountReports
from tims_sheets.account_mapping_table import AccountMappingTable
from tims_sheets.bank_account_data import BankAccountData


def monthly_breakdown_example():
    mapping_table = AccountMappingTable.from_spreadsheet(ACCOUNT_MAPPING_TABLE, force=False, clean=True)
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
    # report.as_table()
    print(f"Breakdown for {Month(2020, 3)}")
    print(tabulate.tabulate(report.as_table(), headers=report.headers()))


def rates_example():
    mapping_table = AccountMappingTable.from_spreadsheet(ACCOUNT_MAPPING_TABLE, force=True, clean=True)
    bank_account_data = BankAccountData \
        .from_spreadsheet(BANK_ACCOUNT_DATA, mapping_table=None, force=False) \
        .with_mapping(mapping_table) \
        .filter_by_date(first_day=Day(2019, 4, 1), last_day=Day(2020, 3, 31))

    report = BankAccountReports.pivot_report(
        bank_account_data=bank_account_data,
        row_fields=[LEVEL_2, LEVEL_3, LEVEL_4, DATE],
        measure_fields=[TRANSACTION_VALUE],
        extra_filter_fields=[],
        filters=[PivotFilter.value_matches(LEVEL_4, OptionalStringPivotValue(Something("Rates")))],
    )
    report.as_table()
    print(tabulate.tabulate(report.as_table(), headers=report.headers()))


if __name__ == '__main__':
    monthly_breakdown_example()
# rates_example()
