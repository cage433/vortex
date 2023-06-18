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
            invoices = list(db.get_invoices(first_issue_date=rng.maybe(invoice.issue_date), last_issue_date=rng.maybe(invoice.issue_date)))
            self.assertEqual(len(invoices), 1)
            self.assertEqual(invoices[0], invoice)

    @RandomisedTest(number_of_runs=20)
    def test_update_invoice(self, rng):
        with TemporaryDirectory() as tmpdir:
            db = VortexSqlite3DB(Path(tmpdir) / "test.db")
            invoice = self.__random_invoice(rng, paid_date=None)
            db.add_invoice(invoice)
            invoices = list(db.get_invoices(first_issue_date=rng.maybe(invoice.issue_date), last_issue_date=rng.maybe(invoice.issue_date)))
            self.assertEqual(len(invoices), 1)
            self.assertEqual(invoices[0], invoice)

            invoice2 = KashflowInvoice(
                invoice.issue_date,
                random_day(rng),
                invoice.reference,
                invoice.external_reference,
                invoice.payment,
                invoice.vat,
                invoice.invoice_type,
                invoice.note,
            )
            db.update_invoice(invoice2)
            invoices = list(db.get_invoices(first_issue_date=rng.maybe(invoice.issue_date), last_issue_date=rng.maybe(invoice.issue_date)))
            self.assertEqual(len(invoices), 1)
            self.assertEqual(invoices[0], invoice2)
