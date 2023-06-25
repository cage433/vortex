from pathlib import Path
from typing import Optional

from bank_statements import Statement, Transaction, BankActivity
from date_range import Day
from env import VORTEX_DB_PATH
from kashflow.invoice import KashflowInvoice
from kashflow.invoices import KashflowInvoices
from sqlite3_db.sqlite3_context import Sqlite3
from utils import checked_type


class VortexSqlite3DB:
    def __init__(self, override_path: Optional[Path] = None):
        self.path: Path = checked_type(override_path or VORTEX_DB_PATH, Path)
        assert self.path.parent.exists(), f"Vortex DB directory {self.path.parent} does not exist"
        self._create_db()

    def _create_db(self):
        with Sqlite3(str(self.path)) as cur:
            cur.execute("""
            CREATE TABLE if not exists kashflow (
                id INTEGER PRIMARY KEY,
                issue_date TEXT NOT NULL,
                paid_date TEXT,
                reference TEXT not null,
                external_reference TEXT,
                payment real not null,
                vat real,
                type TEXT,
                note TEXT
            )
            """)
            res = cur.execute("""
            CREATE TABLE if not exists bank_statements (
                id INTEGER PRIMARY KEY,
                account_id integer not null,
                ftid TEXT not null,
                payment_date TEXT NOT NULL,
                amount real not null,
                transaction_type TEXT not null,
                payee TEXT not null,
                category1 TEXT,
                category2 TEXT
            )
            """)
            res = cur.execute("""
            CREATE TABLE if not exists account_balances (
                id INTEGER PRIMARY KEY,
                account_id integer not null,
                balance_date TEXT NOT NULL,
                balance real not null
            )
            """)

    def add_invoices(self, invoices: KashflowInvoices):
        for inv in invoices.invoices:
            self.add_invoice(inv)

    def add_invoice(
            self,
            invoice: KashflowInvoice
    ):
        with Sqlite3(str(self.path)) as cur:
            cur.execute("""
            INSERT INTO kashflow (issue_date, paid_date, reference, external_reference, payment, vat, type, note)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                invoice.issue_date.iso_repr,
                invoice.paid_date.iso_repr if invoice.paid_date else None,
                invoice.reference,
                invoice.external_reference,
                invoice.payment,
                invoice.vat,
                invoice.invoice_type,
                invoice.note))

    def add_statement(self, statement: Statement):
        with Sqlite3(str(self.path)) as cur:
            for tr in statement.transactions:
                cur.execute("""
                INSERT INTO bank_statements 
                (account_id, ftid, payment_date, amount, transaction_type, payee, category1, category2)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    tr.account,
                    tr.ftid,
                    tr.payment_date.iso_repr,
                    tr.amount,
                    tr.transaction_type,
                    tr.payee,
                    tr.category1,
                    tr.category2
                ))
            for balance_date, balance in statement.balances.items():
                cur.execute("""
                INSERT INTO account_balances 
                (account_id, balance_date, balance)
                VALUES (?, ?, ?)
                """, (
                    statement.account,
                    balance_date.iso_repr,
                    balance,
                ))

    def num_invoices(self) -> int:
        with Sqlite3(str(self.path)) as cur:
            res = cur.execute("SELECT COUNT(*) FROM kashflow")
            return res.fetchone()[0]

    def num_statements(self) -> int:
        with Sqlite3(str(self.path)) as cur:
            res = cur.execute("SELECT COUNT(*) FROM bank_statements")
            return res.fetchone()[0]

    def bank_accounts(self) -> list[int]:
        with Sqlite3(str(self.path)) as cur:
            res = cur.execute("SELECT DISTINCT account_id FROM bank_statements")
            return [row[0] for row in res.fetchall()]

    def get_invoices(self, first_issue_day: Optional[Day], last_issue_day: Optional[Day]) -> KashflowInvoices:
        with Sqlite3(str(self.path)) as cur:
            first_issue_day = first_issue_day or Day(1970, 1, 1)
            last_issue_day = last_issue_day or Day(9999, 12, 31)
            res = cur.execute("""
            SELECT issue_date, paid_date, reference, external_reference, payment, vat, type, note
            FROM kashflow
            WHERE issue_date >= ? AND issue_date <= ?
            """, (first_issue_day.iso_repr, last_issue_day.iso_repr))
            rows = res.fetchall()
            invoices = []
            for row in rows:
                invoices.append(KashflowInvoice(
                    issue_date=Day.parse(row[0]),
                    paid_date=Day.parse(row[1]) if row[1] is not None else None,
                    reference=row[2],
                    external_reference=row[3],
                    payment=row[4],
                    vat=row[5],
                    invoice_type=row[6],
                    note=row[7]
                ))
            return KashflowInvoices(invoices)

    def delete_invoices(self, first_day: Optional[Day] = None, last_day: Optional[Day] = None):
        first_day = first_day or Day(1970, 1, 1)
        last_day = last_day or Day(9999, 12, 31)
        with Sqlite3(str(self.path)) as cur:
            cur.execute("""
            DELETE FROM kashflow
            WHERE issue_date >= ?
            and issue_date <= ?
            """, (
                first_day.iso_repr,
                last_day.iso_repr
            ))

    def delete_statements(self, account_id: int, first_day: Optional[Day] = None, last_day: Optional[Day] = None):
        first_day = first_day or Day(1970, 1, 1)
        last_day = last_day or Day(9999, 12, 31)
        with Sqlite3(str(self.path)) as cur:
            cur.execute("""
            DELETE FROM bank_statements
            WHERE payment_date >= ?
            and payment_date <= ?
            and account_id = ?
            """, (
                first_day.iso_repr,
                last_day.iso_repr,
                account_id
            ))

    def get_statements(self, account_id: int, first_day: Optional[Day] = None,
                       last_day: Optional[Day] = None) -> Statement:
        first_day = first_day or Day(1970, 1, 1)
        last_day = last_day or Day(9999, 12, 31)
        with Sqlite3(str(self.path)) as cur:
            res = cur.execute("""
            SELECT ftid, payment_date, amount, transaction_type, payee, category1, category2
            FROM bank_statements
            WHERE payment_date >= ?
            and payment_date <= ?
            and account_id = ?
            """, (
                first_day.iso_repr,
                last_day.iso_repr,
                account_id
            ))
            rows = res.fetchall()
            transactions = []
            for row in rows:
                transactions.append(Transaction(
                    account=account_id,
                    ftid=row[0],
                    payment_date=Day.parse(row[1]),
                    payee=row[4],
                    amount=float(row[2]),
                    transaction_type=row[3],
                    category1=row[5],
                    category2=row[6]
                ))
            res = cur.execute("""
            SELECT balance_date, balance
            FROM account_balances
            WHERE balance_date >= ?
            and balance_date <= ?
            and account_id = ?
            """, (
                first_day.iso_repr,
                last_day.iso_repr,
                account_id
            ))
            rows = res.fetchall()
            balances = {}
            for row in rows:
                balances[Day.parse(row[0])] = float(row[1])
            return Statement(account_id, transactions, balances)

    def bank_activity(self, first_day: Optional[Day], last_day: Optional[Day]) -> BankActivity:
        first_day = first_day or Day(1970, 1, 1)
        last_day = last_day or Day(9999, 12, 31)
        statements = [self.get_statements(account_id, first_day, last_day) for account_id in self.bank_accounts()]
        return BankActivity(statements)
