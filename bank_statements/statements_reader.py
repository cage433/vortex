import codecs
import shelve
from decimal import Decimal
from pathlib import Path

from ofxparse import OfxParser

import env
from bank_statements import Statement, Transaction
from bank_statements.bank_account import BankAccount, CURRENT_ACCOUNT
from date_range import Day
from date_range.month import Month
from env import STATEMENTS_DIR

__all__ = ["StatementsReader"]

from utils.file_utils import read_csv_file


class StatementsReader:
    SHELF = Path(__file__).parent / "_statements_reader.shelf"

    @staticmethod
    def read_published_balances(statements_dir: Path, force: bool) -> dict[BankAccount, dict[Day, Decimal]]:
        key = f"uncategorised_balances"
        with shelve.open(str(StatementsReader.SHELF)) as shelf:
            if key not in shelf or force:
                balances = {}
                for directory in (statements_dir / "csv").glob("*"):
                    if directory.name == ".DS_Store":
                        continue
                    assert directory.is_dir(), f"Expected {directory} to be a directory"
                    account_id = int(directory.name)
                    account = BankAccount.account_for_id(account_id)
                    csv_files = list(directory.glob("*.csv"))
                    account_balances = {}
                    for file in csv_files:
                        rows = read_csv_file(file)[1:]
                        for row in rows:
                            day = Day.parse(row[0])
                            maybe_balance = row[5]
                            if maybe_balance == "":
                                continue
                            account_balances[day] = Decimal(maybe_balance)
                    balances[account] = account_balances
                shelf[key] = balances
            return shelf[key]

    @staticmethod
    def read_transactions(statements_dir: Path, force: bool) -> dict[BankAccount, list[Transaction]]:
        key = f"uncategorised_transactions"
        with shelve.open(str(StatementsReader.SHELF)) as shelf:
            if key not in shelf or force:
                transactions_by_account = {}
                for directory in (statements_dir / "csv").glob("*"):
                    if directory.name == ".DS_Store":
                        continue
                    assert directory.is_dir(), f"Expected {directory} to be a directory"
                    account_id = int(directory.name)
                    account = BankAccount.account_for_id(account_id)
                    csv_files = list(directory.glob("*.csv"))
                    transactions_for_account = []
                    for file in csv_files:
                        rows = read_csv_file(file)[1:]
                        for row in rows:
                            day = Day.parse(row[0])
                            payee = row[2]
                            paid_out = Decimal(row[3]) if row[3] != "" else Decimal(0)
                            paid_in = Decimal(row[4]) if row[4] != "" else Decimal(0)
                            amount = paid_in - paid_out
                            trans = Transaction(
                                account,
                                day,
                                payee,
                                amount,
                            )
                            transactions_for_account.append(trans)
                    transactions_by_account[account] = transactions_for_account
                shelf[key] = transactions_by_account
            return shelf[key]
        pass

    @staticmethod
    def read_transactions_ofx(statements_dir: Path, force: bool) -> dict[BankAccount, list[Transaction]]:
        key = f"uncategorised_transactions"
        with shelve.open(str(StatementsReader.SHELF)) as shelf:
            if key not in shelf or force:
                transactions_by_account = {}
                for directory in (statements_dir / "ofx").glob("*"):
                    if directory.name == ".DS_Store":
                        continue
                    assert directory.is_dir(), f"Expected {directory} to be a directory"
                    account_id = int(directory.name)
                    account = BankAccount.account_for_id(account_id)
                    ofx_files = list(directory.glob("*.ofx"))
                    transactions_for_account = []
                    for file in ofx_files:
                        with codecs.open(file) as fileobj:
                            ofx = OfxParser.parse(fileobj)
                        for tr in ofx.account.statement.transactions:
                            trans = Transaction(
                                account,
                                Day.from_date(tr.date),
                                tr.payee,
                                Decimal(tr.amount),
                                tr.type,
                            )
                            transactions_for_account.append(trans)
                    transactions_by_account[account] = transactions_for_account
                shelf[key] = transactions_by_account
            return shelf[key]
        pass

    @staticmethod
    def read_statements(force: bool) -> list[Statement]:
        balances_by_account = StatementsReader.read_published_balances(STATEMENTS_DIR, force)
        transactions_by_account = StatementsReader.read_transactions(STATEMENTS_DIR, force)
        assert set(balances_by_account.keys()) == set(transactions_by_account.keys()), \
            "Expected balances and transactions to have the same accounts"
        return [
            Statement(
                account,
                transactions_by_account[account],
                balances_by_account[account]
            )
            for account in balances_by_account.keys()
        ]



if __name__ == '__main__':
    force = True
    balances_by_account = StatementsReader.read_published_balances(STATEMENTS_DIR, force)
    current_account_balances = balances_by_account[CURRENT_ACCOUNT]
    transactions_by_account = StatementsReader.read_transactions(STATEMENTS_DIR, force)
    current_account_transactions = transactions_by_account[CURRENT_ACCOUNT]
    ca_trans_in_sep = sorted(
        [t for t in current_account_transactions if t.payment_date.month == Month(2024, 9)],
        key = lambda t: t.payment_date
    )
    for t in ca_trans_in_sep:
        print(t)
    keys = sorted(list(current_account_balances.keys()))
    for k in keys:
        if k.month == Month(2024, 9):
            print(f"{k}: {current_account_balances[k]}")