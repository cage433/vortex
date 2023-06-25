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
        self.transactions: list[Transaction] = checked_list_type(transactions, Transaction)
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

    @property
    def net_flow(self) -> float:
        return sum(t.amount for t in self.transactions)