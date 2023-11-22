from numbers import Number
from typing import Optional

from bank_statements import Transaction
from date_range import Day, DateRange
from utils import checked_list_type, checked_type, checked_dict_type

__all__ = ["Statement"]

from utils.collection_utils import group_into_dict


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
        if len(self.transactions) > 0:
            assert self.initial_balance_date <= self.transactions[
                0].payment_date, f"First balance must be before first transaction"
        self.transactions_by_date: dict[Day, list[Transaction]] = group_into_dict(self.transactions, lambda t: t.payment_date)
        self.payment_dates: list[Day] = sorted(self.transactions_by_date.keys())
        self.check_consistency()

    def check_consistency(self):
        for d1, d2 in zip(self.balance_dates, self.balance_dates[1:]):
            balance1 = self.published_balances[d1]
            balance2 = self.published_balances[d2]
            payment_dates = [d for d in self.payment_dates if d1 < d <= d2]
            transaction_sum = sum(
                sum(tr.amount for tr in self.transactions_by_date[d])
                for d in payment_dates
            )
            if abs(balance2 - balance1 - transaction_sum) >= 0.01:
                for d in payment_dates:
                    for tr in self.transactions_by_date[d]:
                        print(tr)
                print("here")
            error = balance2 - balance1 - transaction_sum
            assert abs(balance2 - balance1 - transaction_sum) < 0.01, f"Inconsistent balance {error} between {d1} and {d2}, sum trans {transaction_sum}, balance1 {balance1}, balance2 {balance2}"

    def balance_at_date(self, date: Day) -> float:
        assert self.initial_balance_date <= date, f"Date {date} is before initial balance date {self.initial_balance_date}"
        nearest_date = max(d for d in self.balance_dates if d <= date)
        nearest_balance = self.published_balances[nearest_date]
        subsequent_payment_dates = [d for d in self.payment_dates if nearest_date < d <= date]
        subsequent_transaction_amounts = sum(
            sum(tr.amount for tr in self.transactions_by_date[d])
            for d in subsequent_payment_dates
        )
        return nearest_balance + subsequent_transaction_amounts

    def filter_on_period(self, period: DateRange) -> 'Statement':
        d1 = period.first_day
        d2 = period.last_day
        published_balances = {d:b for d, b in self.published_balances.items() if d1 <= d <= d2}
        if d1 not in published_balances and d1 >= self.initial_balance_date:
            bal1 = self.balance_at_date(d1)
            published_balances[d1] = bal1
        if d2 not in published_balances and d2 >= self.initial_balance_date:
            bal2 = self.balance_at_date(d2)
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
