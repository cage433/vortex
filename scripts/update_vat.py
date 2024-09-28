from airtable_db import VortexDB
from bank_statements.bank_account import CURRENT_ACCOUNT
from date_range.accounting_month import AccountingMonth
from date_range.month import Month
from date_range.simple_date_range import SimpleDateRange
from env import VAT_RETURNS_ID, CURRENT_ACCOUNT_STATEMENTS_ID
from google_sheets import Workbook
from google_sheets.statements.statements_tab import StatementsTab
from google_sheets.vat.vat_returns_tab import VATReturnsTab

def update_tab_for_month(month: Month, force: bool):
    categorized_transactions = []
    months = [month -2, month - 1, month]
    accounting_months = [AccountingMonth.from_calendar_month(m) for m in months]
    for m in accounting_months:
        categorized_transactions += StatementsTab(
            Workbook(CURRENT_ACCOUNT_STATEMENTS_ID),
            CURRENT_ACCOUNT,
            m.month_name,
            m
        ).transaction_infos_from_tab()

    period = SimpleDateRange(accounting_months[0].first_day, accounting_months[-1].last_day)

    tab = VATReturnsTab(Workbook(VAT_RETURNS_ID), months)
    gigs_infos = [
        VortexDB().gigs_info_for_period(m, force=force)
        for m in accounting_months
        ]
    # for m in accounting_months:
    #     gi = VortexDB().gigs_info_for_period(m, force=force)
    #     print(f"Month: {m}, num gigs {len(gi.contracts_and_events)}, {gi.total_ticket_sales}")
    # print(f"Num contracts: {len(gigs_info.contracts_and_events)}")
    tab.update(categorized_transactions, gigs_infos)

if __name__ == '__main__':
    update_tab_for_month(Month(2023, 8), force=True)
