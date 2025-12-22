from decimal import Decimal
from typing import Optional

from vortex.banking.bank_account import BankAccount
from vortex.banking.category.payee_categories import PayeeCategory
from vortex.date_range import Day
from vortex.utils import checked_type

__all__ = ["Transaction"]


class Transaction:
    def __init__(
            self,
            account: BankAccount,
            category: PayeeCategory,
            payment_date: Day,
            payee: str,
            amount: Decimal,
    ):
        self.account: BankAccount = checked_type(account, BankAccount)
        self.category: PayeeCategory = checked_type(category, PayeeCategory)
        self.payment_date: Day = checked_type(payment_date, Day)
        self.payee: str = checked_type(payee, str)
        self.amount: Decimal = checked_type(amount, Decimal)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __str__(self):
        return f"{self.account.id}: {self.category} {self.payment_date}, {self.payee}, {self.amount}"

    def __hash__(self):
        return hash((self.account, self.category, self.payment_date, self.payee, self.amount))

    def same_except_for_category(self, rhs: 'Transaction'):
        return self.clone(category= PayeeCategory.UNCATEGORISED) == rhs.clone(category= PayeeCategory.UNCATEGORISED)

    def clone(
            self,
            account: Optional[BankAccount] = None,
            category: Optional[PayeeCategory] = None,
            payment_date: Optional[Day] = None,
            payee: Optional[str] = None,
            amount: Optional[float] = None,
    ):
        return Transaction(
            account=account or self.account,
            category=category or self.category,
            payment_date=payment_date or self.payment_date,
            payee=payee or self.payee,
            amount=amount or self.amount,
        )

