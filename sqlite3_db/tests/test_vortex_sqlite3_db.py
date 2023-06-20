from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional
from unittest import TestCase

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

    @RandomisedTest(number_of_runs=20)
    def test_db_creation(self, rng):
        with TemporaryDirectory() as tmpdir:
            db = VortexSqlite3DB(Path(tmpdir) / "test.db")
            invoice = self.__random_invoice(rng, paid_date=rng.maybe(random_day(rng)))
            db.add_invoice(invoice)
            invoices = db.get_invoices(first_issue_day=rng.maybe(invoice.issue_date), last_issue_day=rng.maybe(invoice.issue_date))
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
            invoices = db.get_invoices(first_issue_day=rng.maybe(first_issue_day), last_issue_day=rng.maybe(last_issue_day))
            self.assertEqual(db.num_invoices(), N)

            db.delete_invoices()
            invoices = db.get_invoices(first_issue_day=rng.maybe(first_issue_day), last_issue_day=rng.maybe(last_issue_day))
            self.assertEqual(len(invoices), 0)
