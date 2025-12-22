import sqlite3
from contextlib import closing
from decimal import Decimal
from pathlib import Path

from bank_statements import Transaction, StatementsReader
from bank_statements.transactions import Transactions
from bank_statements.bank_account import BankAccount
from bank_statements.payee_categories import PayeeCategory
from date_range import Day
from env import VORTEX_DB_PATH, STATEMENTS_DIR
from scripts.search_payments import all_transactions_from_tabs


class VortexDB:
    TRANSACTIONS_TABLE = "Transactions"
    CATEGORY = "category"
    ACCOUNT = "account"
    PAYMENT_DATE = "payment_date"
    PAYEE = "payee"
    AMOUNT = "amount"

    BALANCES_TABLE = "Balances"
    BALANCE_DATE = "balance_date"
    BALANCE = "balance"

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.initialize()

    def execute_sql(self, sql):
        with closing(sqlite3.connect(self.db_path)) as con:
            con.execute(sql)
            con.commit()

    def delete_data(self):
        self.execute_sql(f"DELETE FROM {self.TRANSACTIONS_TABLE}")
        self.execute_sql(f"DELETE FROM {self.BALANCES_TABLE}")

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
        result = self.select(f"SELECT COUNT(*) FROM {self.TRANSACTIONS_TABLE}")
        return result[0][0] if result else 0

    def number_of_balances(self) -> int:
        result = self.select(f"SELECT COUNT(*) FROM {self.BALANCES_TABLE}")
        return result[0][0] if result else 0

    def write_balances(self, balances: dict[BankAccount, dict[Day, Decimal]]):
        def rows_for_account(account: BankAccount):
            acc_balances = balances[account]
            acc_balance_days = sorted(acc_balances.keys())
            return [
                [account.name, d.iso_repr, str(acc_balances[d])]
                for d in acc_balance_days
            ]
        rows = []
        accounts = sorted(balances.keys(), key=lambda acc: acc.name)
        for acc in accounts:
            rows += rows_for_account(acc)
        sql = f"""INSERT INTO '{self.BALANCES_TABLE}' 
                    ('{self.ACCOUNT}', '{self.BALANCE_DATE}', '{self.BALANCE}') 
                    VALUES (?, ?, ?)"""
        self.executemany(sql, rows)

    def write_transactions(self, transactions: Transactions):
        def trans_to_row(t: Transaction):
            return [t.category, t.account.name, t.payment_date.iso_repr, t.payee, str(t.amount)]

        rows = [trans_to_row(t) for t in transactions.transactions]
        sql = f"""INSERT INTO '{self.TRANSACTIONS_TABLE}' 
                    ('{self.CATEGORY}', '{self.ACCOUNT}', '{self.PAYMENT_DATE}', '{self.PAYEE}', '{self.AMOUNT}') 
                    VALUES (?, ?, ?, ?, ?)"""
        self.executemany(sql, rows)

    def read_transactions(self) -> Transactions:
        sql = f"""SELECT 
                    {self.CATEGORY}, {self.ACCOUNT}, {self.PAYMENT_DATE}, {self.PAYEE}, {self.AMOUNT} 
                  FROM 
                    {self.TRANSACTIONS_TABLE}"""
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
        sql = f"""CREATE TABLE IF NOT EXISTS {self.TRANSACTIONS_TABLE}
                 (
                     id INTEGER PRIMARY KEY,
                     {self.CATEGORY} TEXT,
                     {self.ACCOUNT} TEXT,
                     {self.PAYMENT_DATE} TEXT,
                     {self.PAYEE} TEXT,
                     {self.AMOUNT} TEXT
                 )"""
        self.execute_sql(sql)

        sql = f"""CREATE TABLE IF NOT EXISTS {self.BALANCES_TABLE}
                 (
                     id INTEGER PRIMARY KEY,
                     {self.ACCOUNT} TEXT,
                     {self.BALANCE_DATE} TEXT,
                     {self.BALANCE} TEXT
                 )"""
        self.execute_sql(sql)

    @staticmethod
    def default() -> 'VortexDB':
        return VortexDB(VORTEX_DB_PATH)


if __name__ == '__main__':
    transactions = all_transactions_from_tabs(force=False)
    balances = StatementsReader.read_published_balances(STATEMENTS_DIR, force=False)

    db = VortexDB.default()
    db.delete_data()
    db.write_transactions(transactions)
    num_trans = db.number_of_transactions()
    db.write_balances(balances)
    num_balances = db.number_of_balances()
    print(f"Num bals {num_balances}")
    transactions2 = db.read_transactions()
    assert num_trans == len(transactions2.transactions)
    assert transactions2 == transactions
    for t1, t2 in zip(transactions2.transactions, transactions.transactions):
        if t1 != t2:
            print(f"Mismatch: {t1} != {t2}")
    print(num_trans)
