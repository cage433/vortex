from bank_statements.bank_account import CURRENT_ACCOUNT
from bank_statements.categorized_transaction import CategorizedTransactions
from date_range import DateRange
from date_range.accounting_month import AccountingMonth
from env import CURRENT_ACCOUNT_STATEMENTS_ID
from google_sheets import Workbook
from google_sheets.statements.statements_tab import StatementsTab


def categorised_transactions_from_tabs(period: DateRange) -> CategorizedTransactions:
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
    return CategorizedTransactions(transactions)
