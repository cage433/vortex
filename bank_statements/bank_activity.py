import shelve
from decimal import Decimal
from pathlib import Path
from typing import Optional, List


from bank_statements import Statement, Transaction

__all__ = ["BankActivity"]

from bank_statements.bank_account import BankAccount, CURRENT_ACCOUNT

from date_range import Day, DateRange
from date_range.accounting_year import AccountingYear
from env import CURRENT_ACCOUNT_ID

from utils import checked_list_type, checked_type
from utils.collection_utils import group_into_dict


class BankActivity:
    def __init__(self, statements: List[Statement]):
        checked_list_type(statements, Statement)
        self.statements: dict[BankAccount, Statement] = {
            statement.account: statement for statement in statements
        }
        self.sorted_transactions: List[Transaction] = sorted(
            [t for s in self.statements.values() for t in s.transactions],
            key=lambda t: (t.payment_date, t.payee),
        )

    @property
    def num_payment_dates(self):
        return len(set([t.payment_date for t in self.sorted_transactions]))

    @property
    def num_transactions(self):
        return len(self.sorted_transactions)

    @property
    def non_empty(self):
        return self.num_transactions > 0

    def net_flow(self, first_day: Optional[Day] = None, last_day: Optional[Day] = None):
        return sum(s.net_flow(first_day, last_day) for s in self.statements.values())

    @property
    def first_date(self):
        return min(
            [s.first_date for s in self.statements.values() if s.first_date is not None]
        )

    @property
    def last_date(self):
        return max(
            [s.last_date for s in self.statements.values() if s.last_date is not None]
        )

    @property
    def initial_balance(self) -> Decimal:
        return sum([statement.earliest_balance for statement in self.statements.values()])

    @property
    def terminal_balance(self) -> Decimal:
        return sum([statement.latest_balance for statement in self.statements.values()])

    def restrict_to_period(self, period: DateRange) -> 'BankActivity':
        return BankActivity([stmt.filter_on_period(period) for stmt in self.statements.values()])

    def balance_at_eod(self, date: Day) -> Decimal:
        return sum([s.balance_at_eod(date) for s in self.statements.values()])

    def balance_at_sod(self, date: Day) -> Decimal:
        return sum([s.balance_at_sod(date) for s in self.statements.values()])

    def payees(self) -> list[str]:
        return sorted(list(set([t.payee for t in self.sorted_transactions])))


    @property
    def transaction_by_category(self):
        return group_into_dict(self.sorted_transactions, lambda t: t.category)

    @property
    def current_account_statement(self):
        return self.statements[CURRENT_ACCOUNT]

    def restrict_to_account(self, account: BankAccount) -> 'BankActivity':
        checked_type(account, BankAccount)
        return BankActivity([self.statements[account]])

    @property
    def total_vat_payments(self):
        # relying on the payee name sucks. Best we can do for now
        return sum([t.amount for t in self.sorted_transactions if "HMRC VAT" in t.payee.upper()])

    SHELF = Path(__file__).parent / "_bank_activity.shelf"

    @staticmethod
    def build(force: bool):
        key = f"bank_activity"
        with shelve.open(str(BankActivity.SHELF)) as shelf:
            if key not in shelf or force:
                from bank_statements import StatementsReader
                statements = StatementsReader.read_statements(force)
                shelf[key] = BankActivity(statements)
            return shelf[key]


if __name__ == '__main__':
    acc = BankActivity.build(force=False)
    acc = acc.restrict_to_period(AccountingYear(2024))
    dodgy_amount = 374.97
    print(f"Dodgy = {dodgy_amount}, with 20% = {dodgy_amount * 1.2}")


    def trans_is_close(t: Transaction) -> bool:
        if abs(abs(t.amount) - abs(dodgy_amount)) < 0.10:
            return True

        if abs(abs(t.amount) - abs(dodgy_amount * 1.2)) < 0.10:
            return True
        return False


    dodgy_transactions = [t for t in acc.sorted_transactions if trans_is_close(t)]
    for t in dodgy_transactions:
        print(t)
