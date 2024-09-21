from date_range import Day
from kashflow.nominal_ledger import NominalLedger

if __name__ == '__main__':
    ledger = NominalLedger.from_latest_csv_file(force=False)
    text = "1972"
    items = [item for item in ledger.ledger_items if
             (text in item.reference.lower() or text in item.narrative.lower())
             and item.date > Day(2024, 1, 1)]
    for item in items:
        print(item)
