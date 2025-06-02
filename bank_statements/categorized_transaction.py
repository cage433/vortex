from decimal import Decimal
from typing import List, Optional

from bank_statements import Transaction
from bank_statements.bank_account import BankAccount
from bank_statements.payee_categories import category_for_transaction, PayeeCategory
from date_range import Day, DateRange
from date_range.simple_date_range import SimpleDateRange
from utils import checked_type, checked_list_type


# Adds a category to a Transaction if possible.
#
# There are some heuristics where a category can be reasonably inferred
# from the transaction details, however this isn't always possible. In any
# case, all categories should be checked manually.
class CategorizedTransaction:
    def __init__(
            self,
            transaction: Transaction,
            category: PayeeCategory,
    ):
        self.transaction: Transaction = checked_type(transaction, Transaction)
        self.category: PayeeCategory = checked_type(category, PayeeCategory)

    def with_category(self, category: PayeeCategory) -> 'CategorizedTransaction':
        return CategorizedTransaction(self.transaction, category)

    def __eq__(self, other):
        if not isinstance(other, CategorizedTransaction):
            return False
        return self.transaction == other.transaction and self.category == other.category

    def __str__(self):
        return f"{self.category}: {self.transaction}"
    @property
    def payment_date(self) -> Day:
        return self.transaction.payment_date

    @property
    def account(self) -> BankAccount:
        return self.transaction.account

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

    @property
    def num_transactions(self) -> int:
        return len(self.transactions)

    @property
    def is_empty(self) -> bool:
        return self.num_transactions == 0

    def restrict_to_category(self, category: PayeeCategory) -> 'CategorizedTransactions':
        return CategorizedTransactions([t for t in self.transactions if t.category == category])

    def restrict_to_period(self, period: DateRange) -> 'CategorizedTransactions':
        return CategorizedTransactions([t for t in self.transactions if period.contains(t.payment_date)])

    def restrict_to_user(self, user: str) -> 'CategorizedTransactions':
        return CategorizedTransactions([t for t in self.transactions if user.lower() in t.payee.lower()])

    @property
    def categories(self) -> List[PayeeCategory]:
        return sorted(list(set([t.category for t in self.transactions])),
                      key=lambda c: "ZZZZ" if c is PayeeCategory.UNCATEGORISED else c.name)

    def total_for(self, *categories):
        return sum(self.restrict_to_category(c).total_amount for c in categories)

    def __add__(self, other: 'CategorizedTransactions') -> 'CategorizedTransactions':
        checked_type(other, CategorizedTransactions)
        trans_set = set(self.transactions)
        other_trans_set = set(other.transactions)
        for t in trans_set:
            assert t not in other_trans_set, f"Duplicate transaction {t}"
        for t in other_trans_set:
            assert t not in trans_set, f"Duplicate transaction {t}"

        return CategorizedTransactions(self.transactions + other.transactions)

    @property
    def total_amount(self) -> Decimal:
        total = Decimal(0)
        for t in self.transactions:
            total += t.amount
        return total

    @property
    def net_ticket_sales(self) -> Decimal:
        return self.restrict_to_category(PayeeCategory.TICKET_SALES).total_amount

    @property
    def period(self) -> Optional[DateRange]:
        if self.is_empty:
            return None
        first_day = min(t.payment_date for t in self.transactions)
        last_day = max(t.payment_date for t in self.transactions)
        return SimpleDateRange(first_day, last_day)
