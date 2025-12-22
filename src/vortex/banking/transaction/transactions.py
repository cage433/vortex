from decimal import Decimal
from typing import List

from vortex.banking.category.payee_categories import PayeeCategory
from vortex.banking.transaction.transaction import Transaction
from vortex.date_range import DateRange
from vortex.utils import checked_list_type, checked_type


class Transactions:
    def __init__(self, transactions: List[Transaction]):
        self.transactions: List[Transaction] = checked_list_type(transactions, Transaction)

    def __eq__(self, other):
        if not isinstance(other, Transactions):
            return False
        if len(self.transactions) != len(other.transactions):
            return False
        return all(t1 == t2 for t1, t2 in zip(self.transactions, other.transactions))

    @property
    def num_transactions(self) -> int:
        return len(self.transactions)

    @property
    def is_empty(self) -> bool:
        return self.num_transactions == 0

    def restrict_to_category(self, category: PayeeCategory) -> 'Transactions':
        return Transactions([t for t in self.transactions if t.category == category])

    def restrict_to_categories(self, categories: List[PayeeCategory]) -> 'Transactions':
        return Transactions([t for t in self.transactions if t.category in categories])

    def restrict_to_period(self, period: DateRange) -> 'Transactions':
        return Transactions([t for t in self.transactions if period.contains(t.payment_date)])

    @property
    def categories(self) -> List[PayeeCategory]:
        return sorted(list(set([t.category for t in self.transactions])),
                      key=lambda c: "ZZZZ" if c is PayeeCategory.UNCATEGORISED else c.name)

    def __add__(self, other: 'Transactions') -> 'Transactions':
        checked_type(other, Transactions)
        trans_set = set(self.transactions)
        other_trans_set = set(other.transactions)
        for t in trans_set:
            assert t not in other_trans_set, f"Duplicate transaction {t}"
        for t in other_trans_set:
            assert t not in trans_set, f"Duplicate transaction {t}"

        return Transactions(self.transactions + other.transactions)

    @property
    def total_amount(self) -> Decimal:
        total = Decimal(0)
        for t in self.transactions:
            total += t.amount
        return total

    def total_for(self, *categories):
        return sum(self.restrict_to_category(c).total_amount for c in categories)


