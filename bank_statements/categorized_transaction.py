from typing import Optional

from bank_statements import Transaction
from bank_statements.payee_categories import category_for_transaction
from utils import checked_type, checked_optional_type


# Adds a category to a Transaction.
#
# Although there are some heuristics, the categorization requires
# human intervention to be accurate, hence the `confirmed` flag.
class CategorizedTransaction:
    def __init__(
            self,
            transaction: Transaction,
            category: Optional[str],
            confirmed: bool
    ):
        self.transaction: Transaction = checked_type(transaction, Transaction)
        self.category: Optional[str] = checked_optional_type(category, str)
        self.confirmed: bool = checked_type(confirmed, bool)

    @staticmethod
    def heuristic(transaction: Transaction) -> 'CategorizedTransaction':
        return CategorizedTransaction(
            transaction,
            category_for_transaction(transaction),
            confirmed=False
        )
