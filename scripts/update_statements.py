from decimal import Decimal

from bank_statements import BankActivity
from bank_statements.bank_account import CURRENT_ACCOUNT, BankAccount
from date_range.accounting_month import AccountingMonth
from date_range.month import Month
from date_range.simple_date_range import SimpleDateRange
from google_sheets import Workbook
from google_sheets.statements.statements_tab import StatementsTab
from kashflow.nominal_ledger import NominalLedgerItemType, NominalLedger


def statements_tab_for_month(account: BankAccount, month: AccountingMonth) -> StatementsTab:
    id = StatementsTab.sheet_id_for_account(account, month)
    return StatementsTab(
        Workbook(id),
        account,
        month.month_name,
        month
    )


def statements_consistent(tab: StatementsTab, activity: BankActivity, fail_on_inconsistency: bool) -> bool:
    tab_transactions = [t.transaction for t in tab.categorised_transactions_from_tab()]
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
    bank_activity = BankActivity.build(force=refresh_bank_activity).restrict_to_accounts(account).restrict_to_period(
        month)
    if (not statements_consistent(tab, bank_activity, fail_on_inconsistency=False)) or refresh_sheet:
        tab.update(bank_activity)
    statements_consistent(tab, bank_activity, fail_on_inconsistency=True)


def compare_uncategorized_with_kashflow(account: BankAccount, month: AccountingMonth):
    sheet_id = StatementsTab.sheet_id_for_account(account, month)
    tab = StatementsTab(Workbook(sheet_id), account, month.month_name, month)
    transaction_infos = tab.categorised_transactions_from_tab()
    uncategorized = [t for t in transaction_infos if t.category is None]
    kashflow_period = SimpleDateRange(month.first_day - 30, month.last_day + 30)
    ledger_items = NominalLedger.from_latest_csv_file(force=False).restrict_to_period(kashflow_period).ledger_items

    for t in uncategorized:
        print()
        print(f"Uncategorised transaction {t.transaction}")
        amount = t.transaction.amount
        ex_vat_amount = t.transaction.amount / Decimal(1.2)
        near_ledger_items = [
            l for l in ledger_items
            if abs(l.date.days_since(t.transaction.payment_date)) < 60
               and l.item_type not in [NominalLedgerItemType.INPUT_VAT, NominalLedgerItemType.OUTPUT_VAT]
        ]
        sorted_items_1 = sorted(near_ledger_items, key=lambda i: abs(i.amount - amount))
        possibles1 = sorted_items_1[:20]
        possibles1 = [p for p in possibles1 if abs(p.amount - t.transaction.amount) < 1]
        if len(possibles1) > 0:
            print("Candidate ledger items inc VAT")
            for i in possibles1:
                err = (i.amount - amount).quantize(Decimal('0.01'))
                if i.item_type == NominalLedgerItemType.SPACE_HIRE:
                    short_narrative = ""
                else:
                    short_narrative = i.narrative
                print(f"Diff = {err}, {i.date}, {i.amount}, {i.item_type}, {i.reference}, {short_narrative}")

        sorted_items_2 = sorted(near_ledger_items, key=lambda i: abs(i.amount - ex_vat_amount))
        possibles2 = sorted_items_2[:20]
        possibles2 = [p for p in possibles2 if abs(p.amount - ex_vat_amount) < 1]
        if len(possibles2) > 0:
            print("Candidate ledger items exc VAT")
            for i in possibles2:
                err = (i.amount - ex_vat_amount).quantize(Decimal('0.01'))
                if i.item_type == NominalLedgerItemType.SPACE_HIRE:
                    short_narrative = ""
                else:
                    short_narrative = i.narrative
                print(f"Diff = {err}, {i.date}, {i.amount}, {i.item_type}, {i.reference}, {short_narrative}")
        if len(possibles1) == 0 and len(possibles2) == 0:
            print("No candidates found")


if __name__ == '__main__':
    acc_month = AccountingMonth.from_calendar_month(Month(2023, 9))
    ensure_tab_consistent_with_account(CURRENT_ACCOUNT, acc_month, refresh_bank_activity=True, refresh_sheet=True)
    compare_uncategorized_with_kashflow(CURRENT_ACCOUNT, acc_month)
