from typing import Optional

from bank_statements import Statement

__all__ = ["BankActivity"]

from date_range import Day

from utils import checked_list_type, checked_dict_type


class BankActivity:
    def __init__(self, statements: dict[int, Statement]):
        self.statements: dict[int, Statement] = checked_dict_type(statements, int, Statement)

    def net_flow(self, first_day: Optional[Day] = None, last_day: Optional[Day] = None):
        return sum(s.net_flow(first_day, last_day) for s in self.statements.values())

    def sorted_transactions(self):
        return sorted(
            [t for s in self.statements.values() for t in s.transactions],
            key=lambda t: abs(t.amount),
        )

    @property
    def initial_balance(self) -> float:
        return sum([statement.earliest_balance for statement in self.statements.values()])
