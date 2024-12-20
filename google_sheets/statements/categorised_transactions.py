import shelve
from pathlib import Path

from pyasn1.type.univ import Boolean

from bank_statements.bank_account import CURRENT_ACCOUNT
from bank_statements.categorized_transaction import CategorizedTransactions
from date_range import DateRange
from date_range.accounting_month import AccountingMonth
from env import CURRENT_ACCOUNT_STATEMENTS_ID
from google_sheets import Workbook
from google_sheets.statements.statements_tab import StatementsTab


SHELF = Path(__file__).parent / "_categorised_transactions.shelf"

def current_account_transactions_from_tabs(period: DateRange, force: bool) -> CategorizedTransactions:
    key = f"current_account_transactions {period}"
    with shelve.open(str(SHELF)) as shelf:
        if key not in shelf or force:
            acc_month = AccountingMonth.containing(period.first_day)
            last_acc_month = AccountingMonth.containing(period.last_day)
            transactions = []
            while acc_month <= last_acc_month:
                transactions += StatementsTab(
                    Workbook(CURRENT_ACCOUNT_STATEMENTS_ID),
                    CURRENT_ACCOUNT,
                    acc_month.month_name,
                    acc_month
                ).transaction_infos_from_tab()
                acc_month += 1
            shelf[key] = CategorizedTransactions(transactions).restrict_to_period(period)
        return shelf[key]
