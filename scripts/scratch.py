from bank_statements import BankActivity
from bank_statements.bank_account import CURRENT_ACCOUNT
from date_range.accounting_month import AccountingMonth
from date_range.month import Month
from date_range.simple_date_range import SimpleDateRange
from env import AIRTABLE_TOKEN, VORTEX_DATABASE_ID
import requests
import logging

from google_sheets.statements.categorised_transactions import current_account_transactions_from_tabs
from kashflow.nominal_ledger import NominalLedger, NominalLedgerItemType, NominalLedgerItem

if __name__ == '__main__':
    force = False
    month = Month(2025, 2)
    months = [month -2, month - 1, month]
    accounting_months = [AccountingMonth.from_calendar_month(m) for m in months]
    first_day = accounting_months[0].first_day
    last_day = accounting_months[-1].last_day
    period = SimpleDateRange(first_day, last_day)
    categorized_transactions = current_account_transactions_from_tabs(period, force)
    bank_activity = BankActivity.build(force=force).restrict_to_accounts(CURRENT_ACCOUNT).restrict_to_period(period)

    initial_balance = bank_activity.initial_balance
    terminal_balance = bank_activity.terminal_balance

    print(f"Initial balance: {initial_balance}, Terminal balance: {terminal_balance}")
    print(last_day)
    last_day_balance = bank_activity.balance_at_eod(last_day)
    print(f"Last day balance: {last_day_balance}")
    print(last_day_balance - terminal_balance)

    end_jan_balance = bank_activity.balance_at_eod(accounting_months[1].last_day)
    print(f"End Jan balance: {end_jan_balance}")
    print(f"end jan {accounting_months[1].last_day}")
    end_dec_balance = bank_activity.balance_at_eod(accounting_months[0].last_day)
    print(f"End Dec balance: {end_dec_balance}")
    print(f"end Dec {accounting_months[0].last_day}")


