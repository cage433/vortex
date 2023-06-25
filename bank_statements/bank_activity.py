from bank_statements import Statement

__all__ = ["BankActivity"]

from utils import checked_list_type


class BankActivity:
    def __init__(self, statements: list[Statement]):
        self.statements: list[Statement] = checked_list_type(statements, Statement)

    @property
    def net_flow(self):
        return sum(s.net_flow for s in self.statements)

    def sorted_transactions(self):
        return sorted(
            [t for s in self.statements for t in s.transactions],
            key=lambda t: abs(t.amount),
        )