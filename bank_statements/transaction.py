from decimal import Decimal
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
            amount: Decimal,
            transaction_type: str,
    ):
        self.account: int = checked_type(account, int)
        self.ftid = checked_type(ftid, str)
        self.payment_date: Day = checked_type(payment_date, Day)
        self.payee: str = checked_type(payee, str)
        self.amount: Decimal = checked_type(amount, Decimal)
        self.transaction_type: str = checked_type(transaction_type, str)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __str__(self):
        return f"{self.account}: {self.payment_date}, {self.payee}, {self.amount}, {self.transaction_type}"

    def clone(
            self,
            account: Optional[int] = None,
            ftid: Optional[str] = None,
            payment_date: Optional[Day] = None,
            payee: Optional[str] = None,
            amount: Optional[float] = None,
            transaction_type: Optional[str] = None,
    ):
        return Transaction(
            account=account or self.account,
            ftid=ftid or self.ftid,
            payment_date=payment_date or self.payment_date,
            payee=payee or self.payee,
            amount=amount or self.amount,
            transaction_type=transaction_type or self.transaction_type,
        )
