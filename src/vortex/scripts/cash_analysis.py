from tabulate import tabulate

from vortex.banking import BankActivity
from vortex.date_range.month import Month


def do_analysis(force: bool):
    bank_activity = BankActivity.build(force=force)
    m = Month(2023, 1)
    table = []
    while m < Month(2026, 1):
        net_cash = bank_activity.restrict_to_period(m).terminal_balance_across_accounts
        table.append([f"{m.y}/{m.m:02d}", net_cash])
        m += 1
    print(tabulate(table))

def explain_dec():
    m = Month(2025, 12)
    bank_activity = BankActivity.build(force=False).restrict_to_period(m)
    for t in bank_activity.sorted_transactions:
        print(t)

if __name__ == '__main__':
    # explain_dec()
    do_analysis(force=False)