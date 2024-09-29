from decimal import Decimal
from typing import Optional

from bank_statements import Transaction
from bank_statements.payee_categories import category_for_transaction, PayeeCategory
from date_range import Day
from utils import checked_type, checked_optional_type


# Adds a category to a Transaction if possible.
#
# There are some heuristics where a category can be reasonably inferred
# from the transaction details, however this isn't always possible. In any
# case, all categories should be checked manually.
class CategorizedTransaction:
    def __init__(
            self,
            transaction: Transaction,
            category: Optional[PayeeCategory],
    ):
        self.transaction: Transaction = checked_type(transaction, Transaction)
        self.category: Optional[PayeeCategory] = checked_optional_type(category, PayeeCategory)

    @property
    def payment_date(self) -> Day:
        return self.transaction.payment_date

    @property
    def payee(self) -> str:
        return self.transaction.payee

    @property
    def amount(self) -> Decimal:
        return self.transaction.amount

    @staticmethod
    def heuristic(transaction: Transaction) -> 'CategorizedTransaction':
        return CategorizedTransaction(
            transaction,
            category_for_transaction(transaction),
        )
