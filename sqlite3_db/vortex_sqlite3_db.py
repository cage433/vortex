import sqlite3
from pathlib import Path
from typing import Optional

from date_range import Day
from env import VORTEX_DB_PATH
from kashflow.invoice import KashflowInvoice
from sqlite3_db.sqlite3_context import Sqlite3
from utils import checked_type


class VortexSqlite3DB:
    def __init__(self, override_path: Optional[str] = None):
        self.path: Path = checked_type(override_path or VORTEX_DB_PATH, Path)
        assert self.path.parent.exists(), f"Vortex DB directory {self.path.parent} does not exist"
        if not self.path.exists():
            self._create_db()

    def _create_db(self):
        with Sqlite3(str(self.path)) as cur:
            cur.execute("""
            CREATE TABLE kashflow (
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

    def get_invoices(self, first_issue_date: Optional[Day], last_issue_date: Optional[Day]) -> list[KashflowInvoice]:
        with Sqlite3(str(self.path)) as cur:
            first_issue_date = first_issue_date or Day(1970, 1, 1)
            last_issue_date = last_issue_date or Day(9999, 12, 31)
            res = cur.execute("""
            SELECT issue_date, paid_date, reference, external_reference, payment, vat, type, note
            FROM kashflow
            WHERE issue_date >= ? AND issue_date <= ?
            """, (first_issue_date.iso_repr, last_issue_date.iso_repr))
            rows = res.fetchall()
            for row in rows:
                yield KashflowInvoice(
                    issue_date=Day.parse(row[0]),
                    paid_date=Day.parse(row[1]) if row[1] is not None else None,
                    reference=row[2],
                    external_reference=row[3],
                    payment=row[4],
                    vat=row[5],
                    invoice_type=row[6],
                    note=row[7]
                )

    def has_invoice(self, invoice: KashflowInvoice) -> bool:
        with Sqlite3(str(self.path)) as cur:
            res = cur.execute("""
            select count(*) FROM kashflow
            WHERE reference = ?
            and issue_date = ?
            """, (
                invoice.reference,
                invoice.issue_date.iso_repr,
            ))
            num_rows = res.fetchone()[0]
            assert num_rows <= 1, f"Expected 0 or 1 rows, got {num_rows}"
            return num_rows == 1

    def delete_invoice(self, invoice: KashflowInvoice):
        with Sqlite3(str(self.path)) as cur:
            cur.execute("""
            DELETE FROM kashflow
            WHERE reference = ?
            and issue_date = ?
            """, (
                invoice.reference,
                invoice.issue_date.iso_repr,
            ))

    def update_invoice(self, invoice: KashflowInvoice):
        if self.has_invoice(invoice):
            self.delete_invoice(invoice)
        self.add_invoice(invoice)
