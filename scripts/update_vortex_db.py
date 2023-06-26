import os

from bank_statements import StatementsReader
from env import STATEMENTS_DIR, VORTEX_DB_PATH
from kashflow.kashflow_csv import KashflowCSV
from sqlite3_db.vortex_sqlite3_db import VortexSqlite3DB


def update_kashflow_invoices():
    db = VortexSqlite3DB()
    print(f"db has {db.num_invoices()} invoices")
    csv_invoices = KashflowCSV.latest_invoices()
    db.delete_invoices(first_day=csv_invoices.earliest_issue_date, last_day=csv_invoices.latest_issue_date)
    print(f"Post deletion: db has {db.num_invoices()} invoices")
    print(f"Adding {len(csv_invoices)} invoices to database")
    db.add_invoices(csv_invoices)
    print(f"Post insertion: db has {db.num_invoices()} invoices")


def update_bank_statement():
    statements = StatementsReader.read_statements(STATEMENTS_DIR)
    db = VortexSqlite3DB()
    for statement in statements:
        db.delete_statements(statement.account, statement.first_date, statement.last_date)
        db.add_statement(statement)


if __name__ == '__main__':
    os.remove(VORTEX_DB_PATH)
    update_bank_statement()
    update_kashflow_invoices()

    db = VortexSqlite3DB()
    num_statements = db.num_statements()
    print(f"db has {num_statements} statements")
    accounts = db.bank_accounts()
    for acc in accounts:
        print(acc)
