import codecs
from pathlib import Path

from ofxparse import OfxParser

from bank_statements import Statement, Transaction
from date_range import Day
from env import STATEMENTS_DIR

__all__ = ["StatementsReader"]

from utils.file_utils import read_csv_file


class StatementsReader:
    @staticmethod
    def read_balances(statements_dir: Path) -> dict[int, dict[Day, float]]:
        balances = {}
        for dir in (statements_dir / "csv").glob("*"):
            if dir.name == ".DS_Store":
                continue
            assert dir.is_dir(), f"Expected {dir} to be a directory"
            account_id = int(dir.name)
            csv_files = list(dir.glob("*.csv"))
            account_balances = {}
            for file in csv_files:
                rows = read_csv_file(file)[1:]
                for row in rows:
                    day = Day.parse(row[0])
                    maybe_balance = row[5]
                    if maybe_balance == "":
                        continue
                    account_balances[day] = float(maybe_balance)
            balances[account_id] = account_balances
        return balances

    @staticmethod
    def read_transactions(statements_dir: Path) -> dict[int, list[Transaction]]:
        transactions_by_account = {}
        for dir in (statements_dir / "ofx").glob("*"):
            if dir.name == ".DS_Store":
                continue
            assert dir.is_dir(), f"Expected {dir} to be a directory"
            account_id = int(dir.name)
            ofx_files = list(dir.glob("*.ofx"))
            transactions_for_account = []
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
                    transactions_for_account.append(trans)
            transactions_by_account[account_id] = transactions_for_account

        return transactions_by_account

    @staticmethod
    def read_statements(statements_dir: Path) -> list[Statement]:
        balances_by_account = StatementsReader.read_balances(statements_dir)
        transactions_by_account = StatementsReader.read_transactions(statements_dir)
        assert set(balances_by_account.keys()) == set(transactions_by_account.keys()), \
            "Expected balances and transactions to have the same accounts"
        return [
            Statement(
                account_id,
                transactions_by_account[account_id],
                balances_by_account[account_id]
            )
            for account_id in balances_by_account.keys()
        ]


if __name__ == '__main__':
    statements = StatementsReader.read_statements(STATEMENTS_DIR)
    print(len(statements))
