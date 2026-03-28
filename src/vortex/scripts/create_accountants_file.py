from env import ACCOUNTANT_DIR
from vortex.banking import BankActivity
from vortex.banking.account.bank_account import CURRENT_ACCOUNT, SAVINGS_ACCOUNT, BBL_ACCOUNT, CHARITABLE_ACCOUNT
from vortex.date_range import Day
from vortex.date_range.simple_date_range import SimpleDateRange
from vortex.google_sheets.statements.statements_tab import StatementsTab
from vortex.utils.file_utils import write_csv_file

def write_balances(year: int, force: bool):

    period = SimpleDateRange(Day(year - 1, 9, 1), Day(year, 8, 31),)
    
    accounts = [
        CURRENT_ACCOUNT,
        SAVINGS_ACCOUNT,
        BBL_ACCOUNT,
        CHARITABLE_ACCOUNT,
    ]
    activity = BankActivity.build(force)
    table = [
        ["EOD balances"] + [acc.name for acc in accounts],
        ["Date"] + [acc.id for acc in accounts],
    ]
    for d in period.days:
        restricted = activity.restrict_to_period(d)
        row = [d] + [restricted.terminal_balance(acc) for acc in accounts]
        table.append(row)

    name = f"Vortex Balances {year}.csv"
    path = ACCOUNTANT_DIR / name
    write_csv_file(
        path,
        table
    )
def write_transactions_csv(year: int, force: bool):
    period = SimpleDateRange(Day(year - 1, 9, 1), Day(year, 8, 31),)

    transactions = StatementsTab.transactions(period, force=force)
    table = [["Date", "Account", "Account ID", "Category", "Payee", "Amount"]] + [
        [tr.payment_date, tr.account.name, tr.account.id, tr.category, tr.payee, tr.amount]
        for tr in transactions.transactions
    ]
    name = f"Vortex Transactions {year}.csv"
    path = ACCOUNTANT_DIR / name
    write_csv_file(
        path,
        table
    )

if __name__ == '__main__':
    year = 2025
    write_transactions_csv(year, force=False)
    write_balances(year, force=False)
