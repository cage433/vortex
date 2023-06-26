from numbers import Number
from typing import Optional

from date_range import Day
from utils import checked_type, checked_optional_type

__all__ = ["Transaction"]


class Transaction:
    def __init__(
            self,
            account: int,
            ftid: str,
            payment_date: Day,
            payee: str,
            amount: float,
            transaction_type: str,
            category1: Optional[str] = None,
            category2: Optional[str] = None,
    ):
        self.account: int = checked_type(account, int)
        self.ftid = checked_type(ftid, str)
        self.payment_date: Day = checked_type(payment_date, Day)
        self.payee: str = checked_type(payee, str)
        self.amount: float = checked_type(amount, float)
        self.transaction_type: str = checked_type(transaction_type, str)
        self.category1 = checked_optional_type(category1, str)
        self.category2 = checked_optional_type(category2, str)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __str__(self):
        return f"{self.account}: {self.payment_date} {self.payee} {self.amount} {self.transaction_type}"
