from typing import Optional

from bank_statements import Transaction
from date_range import Day
from myopt.opt import Opt


WORK_PERMITS = "Work Permits"
RATES = "Rates"

def _maybe_work_permit(transaction: Transaction) -> Optional[str]:
    payee = transaction.payee.upper().strip()
    if payee.endswith("UKVI UK"):
        return WORK_PERMITS
    if payee.endswith("UKVI CREWE"):
        return WORK_PERMITS
    if "HINGWAN K C COS" in payee:
        return WORK_PERMITS
    if "MR J HILL VJC COS" in payee:
        return WORK_PERMITS
    if "FRUSION MEDIA ACCO COS" in payee:
        return WORK_PERMITS
    if transaction.payment_date == Day(2022, 5, 20) and "K HINGWAN VORTEX EXPENSESS" in payee:
        return WORK_PERMITS
    if transaction.payment_date == Day(2022, 11, 2) and "DUSTY KNUC" in payee:
        return WORK_PERMITS
    if "KLARNA*COS" in payee:
        return WORK_PERMITS
    if "KLARNA*WWW" in payee:
        return WORK_PERMITS
    return None


def _maybe_rates(transaction: Transaction) -> Optional[str]:
    payee = transaction.payee.upper().strip().replace(" ", "")
    if "LBHACKNEYRATES" in payee:
        return RATES
    if transaction.payment_date == Day(2023, 7, 21) and "LBHACKNEYGENFUNDVORTEX" in payee:
        return RATES
    return None

def category_for_transaction(transaction: Transaction) -> Opt[str]:
    return Opt.of(
        _maybe_work_permit(transaction) or _maybe_rates(transaction)
    )




