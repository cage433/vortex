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
            category3: Optional[str] = None,
            category4: Optional[str] = None,
    ):
        self.account: int = checked_type(account, int)
        self.ftid = checked_type(ftid, str)
        self.payment_date: Day = checked_type(payment_date, Day)
        self.payee: str = checked_type(payee, str)
        self.amount: float = checked_type(amount, float)
        self.transaction_type: str = checked_type(transaction_type, str)
        self.category1 = checked_optional_type(category1, str)
        self.category2 = checked_optional_type(category2, str)
        self.category3 = checked_optional_type(category3, str)
        self.category4 = checked_optional_type(category4, str)

    def category(self, n: int) -> str:
        if n == 1:
            return self.category1
        if n == 2:
            return self.category2
        if n == 3:
            return self.category3
        if n == 4:
            return self.category4
        raise ValueError(f"Invalid category number: {n}")

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __str__(self):
        return f"{self.account}: {self.payment_date}, {self.payee}, {self.amount}, {self.transaction_type}, {self.category1}, {self.category2}, {self.category3}, {self.category4}"

    def clone(
            self,
            account: Optional[int] = None,
            ftid: Optional[str] = None,
            payment_date: Optional[Day] = None,
            payee: Optional[str] = None,
            amount: Optional[float] = None,
            transaction_type: Optional[str] = None,
            category1: Optional[str] = None,
            category2: Optional[str] = None,
            category3: Optional[str] = None,
            category4: Optional[str] = None,
    ):
        return Transaction(
            account=account or self.account,
            ftid=ftid or self.ftid,
            payment_date=payment_date or self.payment_date,
            payee=payee or self.payee,
            amount=amount or self.amount,
            transaction_type=transaction_type or self.transaction_type,
            category1=category1 or self.category1,
            category2=category2 or self.category2,
            category3=category3 or self.category3,
            category4=category4 or self.category4,
        )
