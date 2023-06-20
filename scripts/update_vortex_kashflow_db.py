from kashflow.kashflow_csv import KashflowCSV
from sqlite3_db.vortex_sqlite3_db import VortexSqlite3DB


def update_vortex_kashflow_db():
    db = VortexSqlite3DB()
    db_invoices = db.get_invoices(None, None)
    csv_invoices = KashflowCSV.latest_invoices()
    new_invoices = db_invoices.new_invoices(csv_invoices)
    modified_invoices = db_invoices.modified_invoices(csv_invoices)
    for invoice in new_invoices:
        db.add_invoice(invoice)
    for invoice in modified_invoices:
        db.update_invoice(invoice)


if __name__ == '__main__':
    update_vortex_kashflow_db()
