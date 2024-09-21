from decimal import Decimal

from accounting.accounting_activity import AccountingActivity
from bank_statements import BankActivity
from bank_statements.bank_account import CURRENT_ACCOUNT, BankAccount
from date_range import DateRange
from date_range.accounting_month import AccountingMonth
from date_range.month import Month
from date_range.simple_date_range import SimpleDateRange
from env import CURRENT_ACCOUNT_ID, CURRENT_ACCOUNT_STATEMENTS_ID
from google_sheets import Workbook
from google_sheets.statements.statements_tab import StatementsTab
from kashflow.nominal_ledger import NominalLedgerItemType
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
        if l != r:
            if fail_on_inconsistency:
                raise ValueError(f"Error: transactions mismatch: {l} != {r}")
            return False
    return True


def ensure_tab_consistent_with_account(account: BankAccount, month: AccountingMonth, refresh_bank_activity: bool,
                                       refresh_sheet: bool):
    tab = statements_tab_for_month(account, month)
    bank_activity = BankActivity.build(force=refresh_bank_activity).restrict_to_account(account).restrict_to_period(
        month)
    if (not statements_consistent(tab, bank_activity, fail_on_inconsistency=False)) or refresh_sheet:
        tab.update(bank_activity)
    statements_consistent(tab, bank_activity, fail_on_inconsistency=True)


def compare_uncategorized_with_kashflow(account: BankAccount, month: AccountingMonth):
    tab = StatementsTab(Workbook(_sheet_id_for_account(account)), account, month.month_name, month)
    transaction_infos = tab.transaction_infos_from_tab()
    uncategorized = [t for t in transaction_infos if t.category is None]
    kashflow_period = SimpleDateRange(month.first_day - 30, month.last_day + 30)
    ledger_items = AccountingActivity.activity_for_period(kashflow_period, force=False, force_bank=False,
                                                      force_nominal_ledger=False).nominal_ledger.ledger_items

    for t in uncategorized:
        print()
        print(f"Candidate invoice for {t.transaction}")
        amount = t.transaction.amount
        ex_vat_amount = t.transaction.amount / Decimal(1.2)
        near_ledger_items = [
            l for l in ledger_items
            if abs(l.date.days_since(t.transaction.payment_date)) < 60
               and l.item_type not in [NominalLedgerItemType.INPUT_VAT, NominalLedgerItemType.OUTPUT_VAT]
        ]
        sorted_items_1 = sorted(near_ledger_items, key=lambda i: abs(i.amount - amount))
        sorted_items_2 = sorted(near_ledger_items, key=lambda i: abs(i.amount - ex_vat_amount))
        print("Sorted items inc VAT")
        possibles = sorted_items_1[:20]
        possibles = [p for p in possibles if abs(p.amount - t.transaction.amount) < 1]
        for i in possibles:
            err = (i.amount - amount).quantize(Decimal('0.01'))
            print(f"Diff = {err}, {i}")
        print("Sorted items exc VAT")
        possibles = sorted_items_2[:20]
        possibles = [p for p in possibles if abs(p.amount - ex_vat_amount) < 1]
        for i in possibles:
            err = (i.amount - ex_vat_amount).quantize(Decimal('0.01'))
            print(f"Diff = {err}, {i}")



if __name__ == '__main__':
    month = AccountingMonth.from_calendar_month(Month(2024, 3))
    ensure_tab_consistent_with_account(CURRENT_ACCOUNT, month, refresh_bank_activity=False, refresh_sheet=True)
    compare_uncategorized_with_kashflow(CURRENT_ACCOUNT, month)
