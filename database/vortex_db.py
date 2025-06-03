import sqlite3
from contextlib import closing
from decimal import Decimal
from pathlib import Path

from bank_statements import Transaction
from bank_statements.Transactions import Transactions
from bank_statements.bank_account import BankAccount
from bank_statements.payee_categories import PayeeCategory
from date_range import Day
from env import VORTEX_DB_PATH
from scripts.search_payments import all_transactions_from_tabs


class VortexDB:
    CATEGORY = "category"
    ACCOUNT = "account"
    PAYMENT_DATE = "payment_date"
    PAYEE = "payee"
    AMOUNT = "amount"

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.initialize()

    def execute_sql(self, sql):
        with closing(sqlite3.connect(self.db_path)) as con:
            con.execute(sql)
            con.commit()

    def delete_transactions(self):
        self.execute_sql("DELETE FROM categorised_transactions")

    def executemany(self, sql, values):
        with closing(sqlite3.connect(self.db_path)) as con:
            con.executemany(sql, values)
            con.commit()

    def select(self, sql):
        with closing(sqlite3.connect(self.db_path)) as con:
            cur = con.cursor()
            cur.execute(sql)
            return cur.fetchall()

    def number_of_transactions(self) -> int:
        result = self.select("SELECT COUNT(*) FROM categorised_transactions")
        return result[0][0] if result else 0

    def write_categorised_transactions(self, transactions: Transactions):
        def trans_to_row(t: Transaction):
            return [t.category, t.account.name, t.payment_date.iso_repr, t.payee, str(t.amount)]

        rows = [trans_to_row(t) for t in transactions.transactions]
        sql = f"""INSERT INTO 'categorised_transactions' ('{VortexDB.CATEGORY}', '{VortexDB.ACCOUNT}', '{VortexDB.PAYMENT_DATE}', '{VortexDB.PAYEE}', '{VortexDB.AMOUNT}') VALUES (?, ?, ?, ?, ?)"""
        self.executemany(sql, rows)

    def read_transactions(self) -> Transactions:
        sql = f"SELECT {VortexDB.CATEGORY}, {VortexDB.ACCOUNT}, {VortexDB.PAYMENT_DATE}, {VortexDB.PAYEE}, {VortexDB.AMOUNT} FROM categorised_transactions"
        rows = self.select(sql)
        transactions = []
        for row in rows:
            category, account, payment_date, payee, amount = row
            transaction = Transaction(
                account=BankAccount.from_name(account),
                category=PayeeCategory(category),
                payment_date=Day.parse(payment_date),
                payee=payee,
                amount=Decimal(amount)
            )
            transactions.append(transaction)
        return Transactions(transactions)

    def initialize(self):
        sql = """CREATE TABLE IF NOT EXISTS categorised_transactions
                 (
                     id
                     INTEGER
                     PRIMARY
                     KEY,
                     category
                     TEXT,
                     account
                     TEXT,
                     payment_date
                     TEXT,
                     payee
                     TEXT,
                     amount
                     TEXT
                 )"""
        self.execute_sql(sql)

    @staticmethod
    def default() -> 'VortexDB':
        return VortexDB(VORTEX_DB_PATH)


if __name__ == '__main__':
    transactions = all_transactions_from_tabs(force=True)

    db = VortexDB.default()
    db.delete_transactions()
    db.write_categorised_transactions(transactions)
    num_trans = db.number_of_transactions()
    transactions2 = db.read_transactions()
    assert num_trans == len(transactions2.transactions)
    for t1, t2 in zip(transactions2.transactions, transactions.transactions):
        if t1 != t2:
            print(f"Mismatch: {t1} != {t2}")
    print(num_trans)
