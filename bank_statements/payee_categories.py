from typing import Optional

from bank_statements import Transaction
from date_range import Day
from myopt.opt import Opt

class PayeeCategory:
    WORK_PERMITS = "Work Permits"
    RATES = "Rates"


def _maybe_work_permit(transaction: Transaction) -> Optional[str]:
    payee = transaction.payee
    if any(
            payee.endswith(suffix)
            for suffix in ["UKVI UK", "UKVI Crewe", ]
    ):
        return PayeeCategory.WORK_PERMITS
    if any(
            text in payee
            for text in [
                "HINGWAN K C COS",
                "Mr J Hill VJC COS",
                "Frusion Media Acco COS",
                "Klarna*COS",
                "Klarna*www"
            ]
    ):
        return PayeeCategory.WORK_PERMITS

    if transaction.payment_date == Day(2022, 5, 20) and "K HINGWAN VORTEX EXPENSESS" in payee:
        return PayeeCategory.WORK_PERMITS
    if transaction.payment_date == Day(2022, 11, 2) and "DUSTY KNUC" in payee:
        return PayeeCategory.WORK_PERMITS
    return None


def _maybe_rates(transaction: Transaction) -> Optional[str]:
    payee = transaction.payee
    if "LB Hackney rates" in payee:
        return PayeeCategory.RATES
    if transaction.payment_date == Day(2023, 7, 21) and "LB HACKNEY GENFUND VORTEX" in payee:
        return PayeeCategory.RATES
    return None


def category_for_transaction(transaction: Transaction) -> Opt[str]:
    return Opt.of(
        _maybe_work_permit(transaction) or
        _maybe_rates(transaction)
    )
