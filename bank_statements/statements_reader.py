import codecs
from pathlib import Path

from ofxparse import OfxParser

from bank_statements import Statement, Transaction
from date_range import Day
from env import STATEMENTS_DIR

__all__ = ["StatementsReader"]


class StatementsReader:
    @staticmethod
    def read_statements(statements_dir: Path) -> list[Statement]:
        statements = []
        for dir in statements_dir.glob("*"):
            if dir.name == ".DS_Store":
                continue
            assert dir.is_dir(), f"Expected {dir} to be a directory"
            account_id = int(dir.name)
            ofx_files = list(dir.glob("*.ofx"))
            transactions = []
            for file in ofx_files:
                with codecs.open(file) as fileobj:
                    ofx = OfxParser.parse(fileobj)
                for tr in ofx.account.statement.transactions:
                    trans = Transaction(
                        account_id,
                        tr.id,
                        Day.from_date(tr.date),
                        tr.payee,
                        float(tr.amount),
                        tr.type
                    )
                    transactions.append(trans)
            statements.append(Statement(account_id, transactions))

        return statements


if __name__ == '__main__':
    statements = StatementsReader.read_statements(STATEMENTS_DIR)
    print(len(statements))
