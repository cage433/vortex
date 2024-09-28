from bank_statements import BankActivity
from env import AIRTABLE_TOKEN, VORTEX_DATABASE_ID
import requests
import logging

if __name__ == '__main__':
    acc = BankActivity.build(force=False)
    for t in acc.sorted_transactions:
        if "go" in t.payee.lower():
            print(t)

