from typing import Optional

from bank_statements import Transaction
from bank_statements.payee_categories import category_for_transaction
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
            category: Optional[str],
    ):
        self.transaction: Transaction = checked_type(transaction, Transaction)
        self.category: Optional[str] = checked_optional_type(category, str)

    @property
    def payment_date(self) -> Day:
        return self.transaction.payment_date

    @staticmethod
    def heuristic(transaction: Transaction) -> 'CategorizedTransaction':
        return CategorizedTransaction(
            transaction,
            category_for_transaction(transaction),
        )
