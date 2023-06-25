from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional
from unittest import TestCase

from bank_statements import Transaction, Statement
from date_range import Day
from date_range.tests.fixtures import random_day
from kashflow.invoice import KashflowInvoice
from sqlite3_db.vortex_sqlite3_db import VortexSqlite3DB
from testing_utils import RandomisedTest
from utils import RandomNumberGenerator


class VortexSqlite3DBTest(TestCase):
    def __random_invoice(self, rng: RandomNumberGenerator, paid_date: Optional[Day]) -> KashflowInvoice:
        return KashflowInvoice(
            random_day(rng),
            paid_date=paid_date,
            reference=rng.choice("test", ""),
            external_reference=rng.maybe(rng.choice("test", "")),
            payment=rng.uniform(0, 100),
            vat=rng.maybe(rng.uniform(0, 100)),
            invoice_type=rng.choice("Mike", "", None),
            note=rng.choice("Test invoice", "", None),
        )

    def __random_transaction(self, rng: RandomNumberGenerator, account_id: int) -> Transaction:
        return Transaction(
            account=account_id,
            ftid=rng.choice("test", ""),
            payment_date=random_day(rng),
            payee=rng.choice("test payee", ""),
            amount=rng.uniform(-100, 100),
            transaction_type=rng.choice("test12", ""),
            category1=rng.maybe(rng.choice("test2", "")),
            category2=rng.maybe(rng.choice("test3", ""))
        )

    @RandomisedTest(number_of_runs=20)
    def test_db_creation(self, rng):
        with TemporaryDirectory() as tmpdir:
            db = VortexSqlite3DB(Path(tmpdir) / "test.db")
            invoice = self.__random_invoice(rng, paid_date=rng.maybe(random_day(rng)))
            db.add_invoice(invoice)
            invoices = db.get_invoices(first_issue_day=rng.maybe(invoice.issue_date),
                                       last_issue_day=rng.maybe(invoice.issue_date))
            self.assertEqual(len(invoices), 1)
            self.assertTrue(invoices.has_invoice(invoice))

    @RandomisedTest(number_of_runs=20)
    def test_invoice_deletion(self, rng):
        with TemporaryDirectory() as tmpdir:
            db = VortexSqlite3DB(Path(tmpdir) / "test.db")
            N = rng.randint(1, 10)
            invoices = [self.__random_invoice(rng, paid_date=None) for _ in range(N)]
            for inv in invoices:
                db.add_invoice(inv)
            self.assertEqual(db.num_invoices(), N)

            first_issue_day = min(inv.issue_date for inv in invoices)
            last_issue_day = max(inv.issue_date for inv in invoices)
            db.delete_invoices(first_day=last_issue_day + 1)
            self.assertEqual(db.num_invoices(), N)

            db.delete_invoices(last_day=first_issue_day - 1)
            self.assertEqual(db.num_invoices(), N)

            db.delete_invoices()
            self.assertEqual(db.num_invoices(), 0)

    @RandomisedTest(number_of_runs=20)
    def test_statements(self, rng):
        with TemporaryDirectory() as tmpdir:
            db = VortexSqlite3DB(Path(tmpdir) / "test.db")
            N_accounts = rng.randint(1, 10)
            accounts = list(set([rng.randint(0, 100) for _ in range(N_accounts)]))
            N_trans = rng.randint(1, 10)
            statements = [
                Statement(account,
                          [self.__random_transaction(rng, account) for _ in range(N_trans)]
                          )
                for account in accounts

            ]
            for s in statements:
                db.add_statement(s)
            statements2 = [db.get_statements(account_id) for account_id in accounts]
            self.assertEqual(len(statements), len(statements2))
            for s1, s2 in zip(statements, statements2):
                self.assertEqual(len(s1.transactions), len(s2.transactions))
                for t1, t2 in list(zip(s1.transactions, s2.transactions))[0:10]:
                    self.assertEqual(t1, t2)
