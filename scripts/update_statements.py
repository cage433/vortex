from bank_statements import BankActivity
from bank_statements.bank_account import CURRENT_ACCOUNT, BankAccount
from date_range.accounting_month import AccountingMonth
from date_range.month import Month
from env import CURRENT_ACCOUNT_ID, CURRENT_ACCOUNT_STATEMENTS_ID
from google_sheets import Workbook
from google_sheets.statements.statements_tab import StatementsTab
from myopt.nothing import Nothing
from myopt.opt import Opt
from utils.logging import log_message

def _sheet_id_for_account(account: BankAccount):
    if account == CURRENT_ACCOUNT:
        return CURRENT_ACCOUNT_STATEMENTS_ID
    raise ValueError(f"Unrecognized account {account}")

def statements_tab_for_month(account: BankAccount, month: AccountingMonth) -> StatementsTab:
    return StatementsTab(
        Workbook(_sheet_id_for_account(account)),
        account,
        month.month_name,
        month
    )


def statements_consistent(tab: StatementsTab, activity: BankActivity, fail_on_inconsistency: bool) -> bool:
    tab_transactions = [t.transaction for t in tab.transaction_infos_from_tab()]
    activity_transactions = activity.sorted_transactions
    if len(tab_transactions) != len(activity_transactions):
        if fail_on_inconsistency:
            raise ValueError("Error: number of transactions mismatch")
        return False
    for l, r in zip(tab_transactions, activity_transactions):
        if r.category == Nothing():
            if l.category != Opt.of(None):
                log_message(f"Blanking category for {l}")
            l = l.sans_category()
        if l != r:
            if fail_on_inconsistency:
                raise ValueError(f"Error: transactions mismatch: {l} != {r}")
            return False
    return True

def ensure_tab_consistent_with_account(account: BankAccount, month: AccountingMonth, force: bool):
    tab = statements_tab_for_month(account, month)
    bank_activity = BankActivity.build(force=force).restrict_to_account(account.id).restrict_to_period(month)
    if not statements_consistent(tab, bank_activity, fail_on_inconsistency=False) or force:
        tab.update(bank_activity)
    statements_consistent(tab, bank_activity, fail_on_inconsistency=True)


if __name__ == '__main__':
    month = AccountingMonth.from_calendar_month(Month(2024, 1))
    ensure_tab_consistent_with_account(CURRENT_ACCOUNT, month, force=False)
