from typing import Optional

from bank_statements import Transaction
from date_range import Day
from myopt.opt import Opt


class PayeeCategory:
    BANK_FEES = "Bank Fees"
    BANK_INTEREST = "Bank Interest"
    BB_LOAN = "BB Loan"
    CREDIT_CARD_FEES = "Credit Card Fees"
    ELECTRICITY = "Electricity"
    INSURANCE = "Insurance"
    KASHFLOW = "Kashflow"
    RATES = "Rates"
    WORK_PERMITS = "Work Permits"


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
    if "LB Hackney rates" in transaction.payee:
        return PayeeCategory.RATES
    if transaction.payment_date == Day(2023, 7, 21) and "LB HACKNEY GENFUND VORTEX" in transaction.payee:
        return PayeeCategory.RATES
    return None


def _maybe_electricity(transaction: Transaction) -> Optional[str]:
    if "EDF ENERGY" in transaction.payee:
        return PayeeCategory.ELECTRICITY
    return None


def _maybe_insurance(transaction: Transaction) -> Optional[str]:
    if any(
            text in transaction.payee
            for text in [
                "CLOSE-JELF",
                "CLOSE - MARSHCOMM",
            ]
    ):
        return PayeeCategory.INSURANCE
    return None


def _maybe_kashflow(transaction: Transaction) -> Optional[str]:
    if "WWW.KASHFLOW.COM" in transaction.payee:
        return PayeeCategory.KASHFLOW
    return None


def _maybe_cc_fees(transaction: Transaction) -> Optional[str]:
    if "PAS RE CPS" in transaction.payee:
        return PayeeCategory.CREDIT_CARD_FEES
    return None


def _maybe_bb_loan(transaction: Transaction) -> Optional[str]:
    if "HSBC PLC LOANS" in transaction.payee:
        return PayeeCategory.BB_LOAN
    return None


def _maybe_bank_fees(transaction: Transaction) -> Optional[str]:
    if any(
            text in transaction.payee
            for text in [
                "Non-Sterling Transaction Fee",
                "CHARGE RENEWAL FEE",
                "TOTAL CHARGES TO",
            ]
    ):
        return PayeeCategory.BANK_FEES
    return None


def _maybe_bank_interest(transaction: Transaction) -> Optional[str]:
    if "INTEREST TO" in transaction.payee:
        return PayeeCategory.BANK_INTEREST
    return None


def category_for_transaction(transaction: Transaction) -> Opt[str]:
    return Opt.of(
        _maybe_work_permit(transaction) or
        _maybe_rates(transaction) or
        _maybe_electricity(transaction) or
        _maybe_insurance(transaction) or
        _maybe_kashflow(transaction) or
        _maybe_cc_fees(transaction) or
        _maybe_bb_loan(transaction) or
        _maybe_bank_fees(transaction) or
        _maybe_bank_interest(transaction) or
        None
    )
