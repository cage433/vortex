from date_range import Day
from utils import checked_type

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
    ):
        self.account: int = checked_type(account, int)
        self.ftid = checked_type(ftid, str)
        self.payment_date: Day = checked_type(payment_date, Day)
        self.payee: str = checked_type(payee, str)
        self.amount: float = checked_type(amount, float)
        self.transaction_type: str = checked_type(transaction_type, str)
