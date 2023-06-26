from typing import Optional

from bank_statements import Statement

__all__ = ["BankActivity"]

from date_range import Day
from env import CURRENT_ACCOUNT_ID

from utils import checked_dict_type


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

    @property
    def payees(self) -> list[str]:
        return sorted(list(set([t.payee for t in self.sorted_transactions()])))


    @property
    def current_account_statement(self):
        return self.statements[CURRENT_ACCOUNT_ID]