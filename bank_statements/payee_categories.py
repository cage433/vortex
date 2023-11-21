from typing import Optional

from bank_statements import Transaction
from date_range import Day
from myopt.opt import Opt


WORK_PERMITS = "Work Permits"
RATES = "Rates"

def _maybe_work_permit(transaction: Transaction) -> Optional[str]:
    payee = transaction.payee.upper().strip().replace(" ", "")
    if payee.endswith("UKVIUK"):
        return WORK_PERMITS
    if payee.endswith("UKVICREWE"):
        return WORK_PERMITS
    if "HINGWANKCCOS" in payee:
        return WORK_PERMITS
    if "MRJHILLVJCCOS" in payee:
        return WORK_PERMITS
    if "FRUSIONMEDIAACCOCOS" in payee:
        return WORK_PERMITS
    if transaction.payment_date == Day(2022, 5, 20) and "KHINGWANVORTEXEXPENSESS" in payee:
        return WORK_PERMITS
    if transaction.payment_date == Day(2022, 11, 2) and "DUSTYKNUC" in payee:
        return WORK_PERMITS
    if "KLARNA*COSUK" in payee:
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




