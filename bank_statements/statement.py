from numbers import Number
from typing import Optional

from bank_statements import Transaction
from date_range import Day
from utils import checked_list_type, checked_type, checked_dict_type

__all__ = ["Statement"]


class Statement:
    def __init__(
            self,
            account: int,
            transactions: list[Transaction],
            balances: dict[Day, float],
    ):
        self.account: int = checked_type(account, int)
        self.transactions: list[Transaction] = sorted(
            checked_list_type(transactions, Transaction),
            key=lambda t: (t.payment_date, t.payee),
        )
        self.balances: dict[Day, float] = checked_dict_type(balances, Day, Number)
        for tr in transactions:
            assert tr.account == account, \
                f"Transaction {tr} has account {tr.account} but statement has account {account}"

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
        if len(self.balances) == 0:
            return None
        return self.balances[min(self.balances.keys())]

    @property
    def payees(self) -> list[str]:
        return sorted(list(set([t.payee for t in self.transactions])))
