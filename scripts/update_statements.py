from bank_statements import BankActivity
from bank_statements.bank_account import CURRENT_ACCOUNT
from date_range.accounting_month import AccountingMonth
from date_range.month import Month
from env import CURRENT_ACCOUNT_ID, CURRENT_ACCOUNT_STATEMENTS_ID
from google_sheets import Workbook
from google_sheets.statements.statements_tab import StatementsTab


def statements_tab_for_month(account: int, month: AccountingMonth) -> StatementsTab:
    return StatementsTab(
        Workbook(CURRENT_ACCOUNT_STATEMENTS_ID),
        account,
        month.month_name,
        month
    )


def update_sheet(account: int, activity: BankActivity):
    pass


if __name__ == '__main__':
    month = AccountingMonth.from_calendar_month(Month(2024, 1))
    tab = statements_tab_for_month(CURRENT_ACCOUNT, month)
    transactions = tab.transaction_infos_from_tab()
    print(len(transactions))
    bank_activity = BankActivity.build(force=False).restrict_to_account(CURRENT_ACCOUNT_ID).restrict_to_period(month)
    tab.update(bank_activity)
    transactions = tab.transaction_infos_from_tab()
    print(len(transactions))
