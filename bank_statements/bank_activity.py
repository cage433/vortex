from typing import Optional

import tabulate

from bank_statements import Statement

__all__ = ["BankActivity"]

from date_range import Day
from env import CURRENT_ACCOUNT_ID

from utils import checked_dict_type
from utils.collection_utils import group_into_dict


class BankActivity:
    def __init__(self, statements: dict[int, Statement]):
        self.statements: dict[int, Statement] = checked_dict_type(statements, int, Statement)

    def net_flow(self, first_day: Optional[Day] = None, last_day: Optional[Day] = None):
        return sum(s.net_flow(first_day, last_day) for s in self.statements.values())

    def sorted_transactions(self):
        return sorted(
            [t for s in self.statements.values() for t in s.transactions],
            key=lambda t: (t.payment_date, t.payee),
        )

    @property
    def initial_balance(self) -> float:
        return sum([statement.earliest_balance for statement in self.statements.values()])

    @property
    def payees(self) -> list[str]:
        return sorted(list(set([t.payee for t in self.sorted_transactions()])))

    @property
    def current_account_statement(self):
        return self.statements[CURRENT_ACCOUNT_ID]

    def formatted_by_category(self, first_day: Optional[Day] = None, last_day: Optional[Day] = None):
        first_day = first_day or Day(1970, 1, 1)
        last_day = last_day or Day(2100, 1, 1)
        transactions = [t for t in self.sorted_transactions() if first_day <= t.payment_date <= last_day]
        table = []
        def pretty_category(category: Optional[str]) -> str:
            if category is None or category.strip() == "":
                return "Uncategorized"
            return category.strip()
        by_category1 = group_into_dict(transactions, lambda t: pretty_category(t.category(1)))
        for i1, category1 in enumerate(sorted(by_category1.keys())):
            by_category2 = group_into_dict(by_category1[category1], lambda t: pretty_category(t.category(2)))
            for i2, category2 in enumerate(sorted(by_category2.keys())):
                by_category3 = group_into_dict(by_category2[category2], lambda t: pretty_category(t.category(3)))
                for i3, category3 in enumerate(sorted(by_category3.keys())):
                    by_category4 = group_into_dict(by_category3[category3], lambda t: pretty_category(t.category(4)))
                    for i4, category4 in enumerate(sorted(by_category4.keys())):
                        transactions = by_category4[category4]
                        indices = [i1, i2, i3, i4]
                        table.append(
                            [
                                category1 if sum(indices[1:]) == 0 else "",
                                category2 if sum(indices[2:]) == 0 else "",
                                category3 if sum(indices[3:]) == 0 else "",
                                category4,
                                sum([t.amount for t in transactions]),
                                len(transactions),
                            ]
                        )
        print(tabulate.tabulate(table, headers=["Category 1", "Category 2", "Category 3", "Category 4", "Amount", "Count"]))
