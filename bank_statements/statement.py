from numbers import Number
from typing import Optional

from bank_statements import Transaction
from date_range import Day, DateRange
from utils import checked_list_type, checked_type, checked_dict_type

__all__ = ["Statement"]


class Statement:
    def __init__(
            self,
            account: int,
            transactions: list[Transaction],
            published_balances: dict[Day, float],
    ):
        self.account: int = checked_type(account, int)
        self.transactions: list[Transaction] = sorted(
            checked_list_type(transactions, Transaction),
            key=lambda t: (t.payment_date, t.payee),
        )
        self.published_balances: dict[Day, float] = checked_dict_type(published_balances, Day, Number)
        for tr in transactions:
            assert tr.account == account, \
                f"Transaction {tr} has account {tr.account} but statement has account {account}"
        self.balance_dates = sorted(self.published_balances.keys())
        assert len(self.balance_dates) > 0, "Statement must have at least one balance"
        self.initial_balance_date = self.balance_dates[0]
        assert self.initial_balance_date <= self.transactions[
            0].payment_date, f"First balance must be before first transaction"
        self.check_consistency()

    def check_consistency(self):
        for d1, d2 in zip(self.balance_dates, self.balance_dates[1:]):
            balance1 = self.published_balances[d1]
            balance2 = self.published_balances[d2]
            transaction_sum = sum(tr.amount for tr in self.transactions if d1 < tr.payment_date <= d2)
            assert abs(balance2 - balance1 - transaction_sum) < 0.01, "Inconsistent balance"

    def balance_at_date(self, date: Day) -> float:
        assert self.initial_balance_date <= date, f"Date {date} is before initial balance date {self.initial_balance_date}"
        nearest_date = max(d for d in self.balance_dates if d <= date)
        nearest_balance = self.published_balances[nearest_date]
        subsequent_transactions = sum(t.amount for t in self.transactions if nearest_date < t.payment_date <= date)
        return nearest_balance + subsequent_transactions

    def filter_on_period(self, period: DateRange) -> 'Statement':
        d1 = period.first_day
        d2 = period.last_day
        bal1 = self.balance_at_date(d1)
        bal2 = self.balance_at_date(d2)
        published_balances = {d:b for d, b in self.published_balances.items() if d1 <= d <= d2}
        if d1 not in published_balances:
            published_balances[d1] = bal1
        if d2 not in published_balances:
            published_balances[d2] = bal2
        return Statement(
            self.account,
            [t for t in self.transactions if d1 <= t.payment_date <= d2],
            published_balances
        )

    @property
    def first_date(self) -> Optional[Day]:
        if len(self.transactions) == 0:
            return None
        return min(t.payment_date for t in self.transactions)

    @property
    def last_date(self) -> Optional[Day]:
        if len(self.transactions) == 0:
            return None
        return max(t.payment_date for t in self.transactions)

    def net_flow(self, first_day: Optional[Day], last_day: Optional[Day]) -> float:
        first_day = first_day or self.first_date
        last_day = last_day or self.last_date
        return sum(t.amount for t in self.transactions if first_day <= t.payment_date <= last_day)

    @property
    def earliest_balance(self) -> Optional[float]:
        if len(self.published_balances) == 0:
            return None
        return self.published_balances[min(self.published_balances.keys())]

    @property
    def payees(self) -> list[str]:
        return sorted(list(set([t.payee for t in self.transactions])))
