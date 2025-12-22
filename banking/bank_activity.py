import shelve
from decimal import Decimal
from pathlib import Path
from typing import List, Optional

from banking import BankAccountActivity, Transaction

__all__ = ["BankActivity"]

from banking.bank_account import BankAccount

from date_range import DateRange, Day
from date_range.accounting_month import AccountingMonth
from date_range.month import Month
from date_range.simple_date_range import SimpleDateRange

from utils import checked_list_type


class BankActivity:
    def __init__(self, statements: List[BankAccountActivity]):
        checked_list_type(statements, BankAccountActivity)
        self.accounts: List[BankAccount] = sorted(list(set([s.account for s in statements])), key=lambda a: a.name)
        assert len(statements) == len(self.accounts), "Duplicate accounts"
        self.statements: dict[BankAccount, BankAccountActivity] = {
            statement.account: statement
            for statement in statements
        }
        self.sorted_transactions: List[Transaction] = sorted(
            [t for s in self.statements.values() for t in s.transactions],
            key=lambda t: (t.payment_date, t.payee),
        )

    @property
    def num_transactions(self):
        return len(self.sorted_transactions)

    @property
    def non_empty(self):
        return self.num_transactions > 0

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

    def initial_balance(self, account: BankAccount) -> Optional[Decimal]:
        return self.statements[account].earliest_balance

    @property
    def initial_balance_across_accounts(self) -> Decimal:
        return sum([self.initial_balance(acc) for acc in self.accounts]) or Decimal("0")

    def terminal_balance(self, account: BankAccount) -> Decimal:
        return self.statements[account].latest_balance

    @property
    def terminal_balance_across_accounts(self) -> Optional[Decimal]:
        return sum([self.terminal_balance(acc) for acc in self.accounts])

    def restrict_to_period(self, period: DateRange) -> 'BankActivity':
        return BankActivity([stmt.filter_on_period(period) for stmt in self.statements.values()])

    def restrict_to_accounts(self, *accounts) -> 'BankActivity':
        merged_statements = []
        for account in accounts:
            merged_statements.append(self.statements[account])
        return BankActivity(merged_statements)

    SHELF = Path(__file__).parent / "_bank_activity.shelf"

    @staticmethod
    def build(force: bool) -> 'BankActivity':
        key = f"bank_activity"
        with shelve.open(str(BankActivity.SHELF)) as shelf:
            if key not in shelf or force:
                from banking import StatementsReader
                statements = StatementsReader.read_statements(force)
                shelf[key] = BankActivity(statements)
            return shelf[key]


if __name__ == '__main__':
    acc = BankActivity.build(force=False)
    acc_month = AccountingMonth.from_calendar_month(Month(2024, 9))
    acc_at_end_of_month = acc.restrict_to_period(SimpleDateRange(Day(2000, 1, 1), acc_month.last_day))
    print(f"Balance at {acc_month.last_day} = {acc_at_end_of_month.terminal_balance_across_accounts}")
