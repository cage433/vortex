from pathlib import Path
from typing import Optional, List

import tabulate

from bank_statements import Statement, Transaction

__all__ = ["BankActivity"]

from date_range import Day, DateRange
from env import CURRENT_ACCOUNT_ID
from myopt.opt import Opt

from utils import checked_list_type
from utils.collection_utils import group_into_dict


class BankActivity:
    def __init__(self, statements: List[Statement]):
        checked_list_type(statements, Statement)
        self.statements: dict[int, Statement] = {
            statement.account: statement for statement in statements
        }
        self.sorted_transactions: List[Transaction] = sorted(
            [t for s in self.statements.values() for t in s.transactions],
            key=lambda t: (t.payment_date, t.payee),
        )

    def net_flow(self, first_day: Optional[Day] = None, last_day: Optional[Day] = None):
        return sum(s.net_flow(first_day, last_day) for s in self.statements.values())

    @property
    def first_date(self):
        return min(
            [s.first_date for s in self.statements.values() if s.first_date is not None]
        )

    @property
    def initial_balance(self) -> float:
        return sum([statement.earliest_balance for statement in self.statements.values()])

    def restrict_to_period(self, period: DateRange) -> 'BankActivity':
        return BankActivity([stmt.filter_on_period(period) for stmt in self.statements.values()])

    def balance_at_eod(self, date: Day) -> float:
        return sum([s.balance_at_eod(date) for s in self.statements.values()])

    def balance_at_sod(self, date: Day) -> float:
        return sum([s.balance_at_sod(date) for s in self.statements.values()])

    def payees(self) -> list[str]:
        return sorted(list(set([t.payee for t in self.sorted_transactions])))

    def net_amount_for_category(self, category: str):
        return sum([t.amount for t in self.sorted_transactions if t.category.get_or_else("") == category])

    @property
    def current_account_statement(self):
        return self.statements[CURRENT_ACCOUNT_ID]

    def formatted_by_category(self, first_day: Optional[Day] = None, last_day: Optional[Day] = None):
        first_day = first_day or Day(1970, 1, 1)
        last_day = last_day or Day(2100, 1, 1)
        transactions = [t for t in self.sorted_transactions if first_day <= t.payment_date <= last_day]
        table = []

        def pretty_category(category: Opt[str]) -> str:
            if category.get_or_else("").strip() == "":
                return "Uncategorized"
            return category.get().strip()

        by_category = group_into_dict(transactions, lambda t: pretty_category(t.category))
        for category in sorted(by_category.keys()):
            cat_transactions = by_category[category]
            table.append(
                [
                    category,
                    sum([t.amount for t in cat_transactions]),
                    len(cat_transactions),
                ]
            )
        print(tabulate.tabulate(table, headers=["Category", "Amount", "Count"]))

    @staticmethod
    def build(
            statements_dir: Optional[Path] = None,
    ):
        from bank_statements import StatementsReader
        statements = StatementsReader.read_statements(statements_dir)
        return BankActivity(statements)


if __name__ == '__main__':
    acc = BankActivity.build()
    acc.formatted_by_category()
