from bank_statements import BankActivity
from bank_statements.bank_account import CURRENT_ACCOUNT
from env import AIRTABLE_TOKEN, VORTEX_DATABASE_ID
import requests
import logging

from kashflow.nominal_ledger import NominalLedger, NominalLedgerItemType, NominalLedgerItem

if __name__ == '__main__':
    ledger = NominalLedger.from_latest_csv_file(force=False)
    items_for_type = ledger.filter_on_item_type(NominalLedgerItemType.MARKETING_INDIRECT).ledger_items
    by_date = sorted(items_for_type, key=lambda item: item.date)
    for item in by_date:
        print(item)

    bank_activity = BankActivity.build(force=False)
    current_account = bank_activity.statements[CURRENT_ACCOUNT]
    for t in current_account.transactions:
        if "oblong" in t.payee.lower():
            print(t)

