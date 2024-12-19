from decimal import Decimal
from typing import Optional

from bank_statements import Transaction
from bank_statements.payee_categories import category_for_transaction, PayeeCategory
from date_range import Day, DateRange
from utils import checked_type, checked_optional_type, checked_list_type


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


class CategorizedTransactions:
    def __init__(self, transactions: list[CategorizedTransaction]):
        self.transactions: list[CategorizedTransaction] = checked_list_type(transactions, CategorizedTransaction)

    def restrict_to_category(self, category: Optional[PayeeCategory]) -> 'CategorizedTransactions':
        return CategorizedTransactions([t for t in self.transactions if t.category == category])

    def restrict_to_period(self, period: DateRange) -> 'CategorizedTransactions':
        return CategorizedTransactions([t for t in self.transactions if period.contains(t.payment_date)])

    def total_for(self, *categories):
        return sum(self.restrict_to_category(c).total_amount for c in categories)

    @property
    def total_amount(self) -> Decimal:
        return sum(t.amount for t in self.transactions)

    @property
    def net_ticket_sales(self) -> Decimal:
        return self.restrict_to_category(PayeeCategory.TICKET_SALES).total_amount + self.restrict_to_category(
            PayeeCategory.TICKETWEB_CREDITS).total_amount
