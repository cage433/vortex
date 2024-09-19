from pathlib import Path
from typing import Optional

from bank_statements import Transaction
from date_range import Day
from myopt.opt import Opt

def _musicians():
    file = Path(__file__).parent.parent / "resources" / "musicians.txt"
    musicians = []
    with open(file) as f:
        for line in f.readlines():
            musicians.append(line.strip())
    return musicians

MUSICIANS = _musicians()

class PayeeCategory:
    AIRTABLE = "Airtable"
    BANK_FEES = "Bank Fees"
    BANK_INTEREST = "Bank Interest"
    BAR_PURCHASES = "Bar Purchases"
    BAR_SNACKS = "Bar Snacks"
    BB_LOAN = "BB Loan"
    BT = "BT"
    CLEANING = "Cleaning"
    CREDIT_CARD_FEES = "Credit Card Fees"
    ELECTRICITY = "Electricity"
    FIRE_ALARM = "Fire Alarm"
    INSURANCE = "Insurance"
    KASHFLOW = "Kashflow"
    MAILCHIMP = "Mailchimp"
    MARKETING_INDIRECT = "Marketing - Indirect"
    MEMBERSHIPS = "Memberships"
    MUSICIAN_PAYMENTS = "Musician Payments"
    MUSIC_VENUE_TRUST = "Music Venue Trust"
    PETTY_CASH = "Petty cash"
    PIANO_TUNER = "Piano Tuner"
    PRS = "PRS"
    RATES = "Rates"
    SALARIES = "Salaries"
    SECURITY = "Security"
    SLACK = "Slack"
    SOUND_ENGINEER = "Sound Engineer"
    TICKETWEB_CREDITS = "Ticketweb Credits"
    VAT = "VAT"
    WEB_HOST = "Web Host"
    WORK_PERMITS = "Work Permits"
    ZETTLE_CREDITS = "Zettle Credits"


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


def _maybe_rates(transaction: Transaction) -> Optional[str]:
    payee = transaction.payee.lower()
    if "lb hackney rates" in payee or "lbh rates" in payee:
        return PayeeCategory.RATES
    if transaction.payment_date == Day(2023, 7, 21) and "LB HACKNEY GENFUND VORTEX" in transaction.payee:
        return PayeeCategory.RATES


def _maybe_electricity(transaction: Transaction) -> Optional[str]:
    if "EDF ENERGY" in transaction.payee:
        return PayeeCategory.ELECTRICITY


def _maybe_insurance(transaction: Transaction) -> Optional[str]:
    if any(
            text in transaction.payee
            for text in [
                "CLOSE-JELF",
                "CLOSE - MARSHCOMM",
            ]
    ):
        return PayeeCategory.INSURANCE


def _maybe_kashflow(transaction: Transaction) -> Optional[str]:
    if "WWW.KASHFLOW.COM" in transaction.payee:
        return PayeeCategory.KASHFLOW


def _maybe_cc_fees(transaction: Transaction) -> Optional[str]:
    if "PAS RE CPS" in transaction.payee:
        return PayeeCategory.CREDIT_CARD_FEES


def _maybe_bb_loan(transaction: Transaction) -> Optional[str]:
    payee = transaction.payee.lower()
    if payee.startswith("loan ") or " loan" in payee:
        return PayeeCategory.BB_LOAN


def _maybe_petty_cash(transaction: Transaction) -> Optional[str]:
    payee = transaction.payee.lower()
    if "cash halifax" in payee:
        return PayeeCategory.PETTY_CASH

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


def _maybe_bank_interest(transaction: Transaction) -> Optional[str]:
    if "INTEREST TO" in transaction.payee:
        return PayeeCategory.BANK_INTEREST


def _maybe_salaries(transaction: Transaction) -> Optional[str]:
    staff = [
        "pauline le divenac",
        "daniel garel"
    ]
    payee = transaction.payee.lower()
    if any(payee.startswith(name) for name in staff):
        return PayeeCategory.SALARIES


def _maybe_memberships(transaction: Transaction) -> Optional[str]:
    if "Stripe Payments UK" in transaction.payee:
        return PayeeCategory.MEMBERSHIPS


def _maybe_zettle_credits(transaction: Transaction) -> Optional[str]:
    if "PAYPAL PPWDL" in transaction.payee:
        return PayeeCategory.ZETTLE_CREDITS


def _maybe_ticketweb_credits(transaction: Transaction) -> Optional[str]:
    if transaction.payee.startswith("TICKETWEB UK LTD") and transaction.amount > 0:
        return PayeeCategory.TICKETWEB_CREDITS
    return None


def _maybe_bar_purchases(transaction: Transaction) -> Optional[str]:
    payee = transaction.payee.lower()
    companies = [
        "majestic wine",
        "dalston local",
        "flint wines",
        "east london brew",
        "sainsbury"
    ]
    if any(payee.startswith(c) for c in companies):
        return PayeeCategory.BAR_PURCHASES


def _maybe_security(transaction: Transaction) -> Optional[str]:
    if transaction.payee.startswith("Denise Williams"):
        return PayeeCategory.SECURITY


def _maybe_fire_alarm(transaction: Transaction) -> Optional[str]:
    if transaction.payee.lower().startswith("agf fire prot"):
        return PayeeCategory.FIRE_ALARM


def _maybe_vat(transaction: Transaction) -> Optional[str]:
    if transaction.payee.lower().startswith("hmrc vat"):
        return PayeeCategory.VAT


def _maybe_cleaning(transaction: Transaction) -> Optional[str]:
    if transaction.payee.lower().startswith("poolfresh"):
        return PayeeCategory.CLEANING


def _maybe_piano_tuner(transaction: Transaction) -> Optional[str]:
    if transaction.payee.lower().startswith("b sharp pianos"):
        return PayeeCategory.PIANO_TUNER


def _maybe_sound_engineer(tr: Transaction) -> Optional[str]:
    payee = tr.payee.lower()

    def is_multiple_of_ten(amt) -> bool:
        return abs(amt % 10) < 0.01

    known_engineers = [
        "milo mcguire",
        "mike omalley",
        "bella cooper",
        "thomas pew",
        "joe mashiter"
    ]
    if tr.amount < 0 and any(payee.startswith(name) for name in known_engineers):
        return PayeeCategory.SOUND_ENGINEER

def _maybe_prs(tr: Transaction) -> Optional[str]:
    if tr.payee.startswith("PRS "):
        return PayeeCategory.PRS


def _maybe_mailchimp(tr: Transaction) -> Optional[str]:
    if " mailchimp " in tr.payee.lower():
        return PayeeCategory.MAILCHIMP

def _maybe_host(tr: Transaction) -> Optional[str]:
    if tr.payee.lower().startswith("oblong"):
        return PayeeCategory.WEB_HOST

def _maybe_bt(tr: Transaction) -> Optional[str]:
    if tr.payee.lower().startswith("bt group"):
        return PayeeCategory.BT

def _maybe_slack(tr: Transaction) -> Optional[str]:
    payee = tr.payee.lower()
    if payee.startswith("int") and "slack" in payee:
        return PayeeCategory.SLACK

def _maybe_bar_snacks(tr: Transaction) -> Optional[str]:
    payee = tr.payee.lower()
    if payee.startswith("uk bar snacks"):
        return PayeeCategory.BAR_SNACKS

def _maybe_airtable(tr: Transaction) -> Optional[str]:
    payee = tr.payee.lower()
    if payee.startswith("int") and "airtable" in payee:
        return PayeeCategory.AIRTABLE

def _maybe_musician_payments(tr: Transaction) -> Optional[str]:
    payee = tr.payee.lower()
    for m in MUSICIANS:
        if payee.startswith(m) and tr.amount < 0:
            return PayeeCategory.MUSICIAN_PAYMENTS

def _maybe_mvt(tr: Transaction) -> Optional[str]:
    payee = tr.payee.lower()
    if payee.startswith("music venue trust"):
        return PayeeCategory.MUSIC_VENUE_TRUST

def category_for_transaction(transaction: Transaction) -> Opt[str]:
    return Opt.of(
        _maybe_mvt(transaction) or
        _maybe_musician_payments(transaction) or
        _maybe_airtable(transaction) or
        _maybe_petty_cash(transaction) or
        _maybe_bar_snacks(transaction) or
        _maybe_slack(transaction) or
        _maybe_bt(transaction) or
        _maybe_host(transaction) or
        _maybe_mailchimp(transaction) or
        _maybe_prs(transaction) or
        _maybe_sound_engineer(transaction) or
        _maybe_piano_tuner(transaction) or
        _maybe_cleaning(transaction) or
        _maybe_vat(transaction) or
        _maybe_fire_alarm(transaction) or
        _maybe_bar_purchases(transaction) or
        _maybe_security(transaction) or
        _maybe_ticketweb_credits(transaction) or
        _maybe_zettle_credits(transaction) or
        _maybe_salaries(transaction) or
        _maybe_memberships(transaction) or
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
