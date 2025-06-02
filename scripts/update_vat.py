from airtable_db import VortexAirtableDB
from bank_statements import BankActivity
from date_range.accounting_month import AccountingMonth
from date_range.month import Month
from date_range.simple_date_range import SimpleDateRange
from env import VAT_RETURNS_2025_ID
from google_sheets import Workbook
from google_sheets.statements.statements_tab import StatementsTab
from google_sheets.vat.vat_returns_tab import VATReturnsTab

def update_tab_for_month(month: Month, force: bool):
    months = [month -2, month - 1, month]
    accounting_months = [AccountingMonth.from_calendar_month(m) for m in months]
    period = SimpleDateRange(accounting_months[0].first_day, accounting_months[-1].last_day)
    categorized_transactions = StatementsTab.categorized_transactions(period, force)
    bank_activity = BankActivity.build(force=force).restrict_to_period(period)

    tab = VATReturnsTab(Workbook(VATReturnsTab.sheet_id_for_month(accounting_months[-1])), months)
    gigs_info = VortexAirtableDB().gigs_info_for_period(period, force=force)
    tab.update(categorized_transactions.transactions, gigs_info, bank_activity)

if __name__ == '__main__':
    m = Month(2020, 8)
    while m <= Month(2025, 5):
        print(f"Updating VAT return for {m.month_name}")
        update_tab_for_month(m, force=False)
        m += 3
