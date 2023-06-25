from typing import Optional

from bank_statements import Transaction
from date_range import Day
from utils import checked_list_type, checked_type

__all__ = ["Statement"]


class Statement:
    def __init__(self, account: int, transactions: list[Transaction]):
        self.account: int = checked_type(account, int)
        self.transactions: list[Transaction] = checked_list_type(transactions, Transaction)
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
