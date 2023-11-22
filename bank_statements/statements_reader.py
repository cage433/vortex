import codecs
from pathlib import Path
from typing import Optional

import tabulate
from ofxparse import OfxParser

from bank_statements import Statement, Transaction, BankActivity
from bank_statements.payee_categories import category_for_transaction, WORK_PERMITS, RATES
from date_range import Day
from date_range.accounting_month import AccountingMonth
from date_range.accounting_year import AccountingYear
from env import STATEMENTS_DIR, TIMS_MAPPING_CSV

__all__ = ["StatementsReader"]

from myopt.nothing import Nothing
from myopt.opt import Opt
from utils.collection_utils import group_into_dict

from utils.file_utils import read_csv_file, write_csv_file


class StatementsReader:
    @staticmethod
    def read_published_balances(statements_dir: Path) -> dict[int, dict[Day, float]]:
        balances = {}
        for directory in (statements_dir / "csv").glob("*"):
            if directory.name == ".DS_Store":
                continue
            assert directory.is_dir(), f"Expected {directory} to be a directory"
            account_id = int(directory.name)
            csv_files = list(directory.glob("*.csv"))
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
        for directory in (statements_dir / "ofx").glob("*"):
            if directory.name == ".DS_Store":
                continue
            assert directory.is_dir(), f"Expected {directory} to be a directory"
            account_id = int(directory.name)
            ofx_files = list(directory.glob("*.ofx"))
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
                        tr.type,
                        Nothing()
                    )
                    category = category_for_transaction(trans)
                    trans = trans.clone(category=category)
                    transactions_for_account.append(trans)
            transactions_by_account[account_id] = transactions_for_account

        return transactions_by_account

    @staticmethod
    def read_statements(
            statements_dir: Optional[Path] = None,
    ) -> list[Statement]:
        statements_dir = statements_dir or STATEMENTS_DIR
        balances_by_account = StatementsReader.read_published_balances(statements_dir)
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
    month = AccountingMonth(AccountingYear(2023), 10)
    statements = StatementsReader.read_statements(STATEMENTS_DIR)
    bank_activity = BankActivity(statements)#.restrict_to_period(AccountingYear(2023))
    table = []
    for t in bank_activity.sorted_transactions:
        table.append([t.payment_date, t.payee, t.amount])
    write_csv_file(Path("/Users/alex/Downloads/transactions.csv"), table)
    trans = [
        tr for tr in bank_activity.sorted_transactions
        if tr.category == Opt.of(WORK_PERMITS)
    ]
    total = sum(t.amount for t in trans)
    print(f"total = {total}")
    table = []
    tr_by_month = group_into_dict(trans, lambda t: AccountingMonth.containing(t.payment_date))
    # months = sorted(tr_by_month.keys())
    # for m in months:
    #     print(f"{m} {len(tr_by_month[m])}, {sum(t.amount for t in tr_by_month[m])}")
    for tr in trans:
        acc_month = AccountingMonth.containing(tr.payment_date)
        table.append([
            acc_month,
            tr.payment_date,
            tr.payee,
            tr.amount,
        ])
    print(tabulate.tabulate(table))
    print(len(trans))
