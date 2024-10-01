from pathlib import Path
from typing import Optional, List
from enum import Enum, StrEnum, verify, UNIQUE

from bank_statements import Transaction
from date_range import Day
from myopt.opt import Opt
from utils import checked_list_type, checked_type


def _musicians():
    file = Path(__file__).parent.parent / "resources" / "musicians.txt"
    musicians = []
    with open(file) as f:
        for line in f.readlines():
            musicians.append(line.strip())
    return musicians


MUSICIANS = _musicians()


@verify(UNIQUE)
class PayeeCategory(StrEnum):
    ADMINISTRATION = "Administration"
    AIRTABLE = "Airtable"
    BANK_FEES = "Bank Fees"
    BANK_INTEREST = "Bank Interest"
    BAR_STOCK = "Bar Stock"
    BAR_SNACKS = "Bar Snacks"
    BB_LOAN = "BB Loan"
    BT = "BT"
    BUILDING_MAINTENANCE = "Building Maintenance"
    BUILDING_SECURITY = "Building Security"
    CLEANING = "Cleaning"
    CREDIT_CARD_FEES = "Credit Card Fees"
    DONATION = "Donation"
    ELECTRICITY = "Electricity"
    EQUIPMENT_HIRE = "Equipment Hire"
    EQUIPMENT_MAINTENANCE = "Equipment Maintenance"
    EQUIPMENT_PURCHASE = "Equipment Purchase"
    FIRE_ALARM = "Fire Alarm"
    FLOOD = "Flood"
    INSURANCE = "Insurance"
    INTERNAL_TRANSFER = "Internal Transfer"
    KASHFLOW = "Kashflow"
    MAILCHIMP = "Mailchimp"
    LICENSING_DIRECT = "Licensing - Direct"
    LICENSING_INDIRECT = "Licensing - Indirect"
    MARKETING_DIRECT = "Marketing - Direct"
    MARKETING_INDIRECT = "Marketing - Indirect"
    MEMBERSHIPS = "Memberships"
    MUSICIAN_COSTS = "Musician Costs"
    MUSICIAN_PAYMENTS = "Musician Payments"
    MUSIC_VENUE_TRUST = "Music Venue Trust"
    OPERATIONAL_COSTS = "Operational Costs"
    PETTY_CASH = "Petty cash"
    PIANO_TUNER = "Piano Tuner"
    PRS = "PRS"
    RATES = "Rates"
    RENT = "Rent"
    SALARIES = "Salaries"
    SECURITY = "Security"
    SERVICES = "Services"
    SLACK = "Slack"
    SOUND_ENGINEER = "Sound Engineer"
    SPACE_HIRE = "Space Hire"
    SUBSCRIPTIONS = "Subscriptions"
    TELEPHONE = "Telephone"
    THAMES_WATER = "Thames Water"
    TICKETWEB_CREDITS = "Ticketweb Credits"
    VAT = "VAT"
    WEB_HOST = "Web Host"
    WORK_PERMITS = "Work Permits"
    ZETTLE_CREDITS = "Zettle Credits"

    @staticmethod
    def is_subject_to_vat(category: Optional['PayeeCategory']) -> bool:
        if category in [
            PayeeCategory.BB_LOAN, PayeeCategory.BANK_INTEREST, PayeeCategory.CREDIT_CARD_FEES,
            PayeeCategory.DONATION, PayeeCategory.INTERNAL_TRANSFER,
            PayeeCategory.MUSIC_VENUE_TRUST, PayeeCategory.MUSICIAN_PAYMENTS, PayeeCategory.PETTY_CASH,
            PayeeCategory.RATES, PayeeCategory.SALARIES, PayeeCategory.SOUND_ENGINEER,
            PayeeCategory.VAT, PayeeCategory.WORK_PERMITS
        ]:
            return False

        if category in [
            PayeeCategory.ADMINISTRATION,
            PayeeCategory.AIRTABLE, PayeeCategory.BANK_FEES, PayeeCategory.BAR_SNACKS,
            PayeeCategory.BAR_STOCK, PayeeCategory.BT, PayeeCategory.BUILDING_MAINTENANCE, PayeeCategory.BUILDING_SECURITY,
            PayeeCategory.CLEANING, PayeeCategory.ELECTRICITY,
            PayeeCategory.EQUIPMENT_HIRE, PayeeCategory.EQUIPMENT_MAINTENANCE, PayeeCategory.EQUIPMENT_PURCHASE,
            PayeeCategory.FIRE_ALARM, PayeeCategory.FLOOD,
            PayeeCategory.INSURANCE, PayeeCategory.KASHFLOW,
            PayeeCategory.LICENSING_DIRECT, PayeeCategory.LICENSING_INDIRECT,
            PayeeCategory.MAILCHIMP, PayeeCategory.MARKETING_DIRECT, PayeeCategory.MARKETING_INDIRECT,
            PayeeCategory.MEMBERSHIPS, PayeeCategory.MUSICIAN_COSTS, PayeeCategory.OPERATIONAL_COSTS,
            PayeeCategory.PRS, PayeeCategory.PIANO_TUNER, PayeeCategory.RENT, PayeeCategory.SECURITY,
            PayeeCategory.SERVICES, PayeeCategory.SLACK, PayeeCategory.SPACE_HIRE, PayeeCategory.SUBSCRIPTIONS,
            PayeeCategory.TELEPHONE, PayeeCategory.THAMES_WATER,
            PayeeCategory.TICKETWEB_CREDITS, PayeeCategory.WEB_HOST, PayeeCategory.ZETTLE_CREDITS
        ]:
            return True

        if category is False:
            return False

    @staticmethod
    def is_credit(category: Optional['PayeeCategory']) -> bool:
        return category in [PayeeCategory.ZETTLE_CREDITS, PayeeCategory.TICKETWEB_CREDITS, PayeeCategory.SPACE_HIRE]

    @staticmethod
    def is_debit(category: Optional['PayeeCategory']) -> bool:
        return not PayeeCategory.is_credit(category)


def matches_start(transaction, matches: any) -> bool:
    if isinstance(matches, str):
        matches = [matches]
    payee = transaction.payee.lower()
    for match in matches:
        if payee.startswith(match):
            return True
    return False


def matches_anywhere(transaction, matches: any) -> bool:
    if isinstance(matches, str):
        matches = [matches]
    payee = transaction.payee.lower()
    for match in matches:
        if match in payee:
            return True
    return False


def _maybe_work_permit(transaction: Transaction) -> Optional[str]:
    if matches_anywhere(
            transaction,
            [
                "ukvi uk",
                "ukvi crewe",
                "hingwan k c cos",
                "mr j hill vjc cos",
                "frusion media acco cos",
                "klarna*cos",
                "klarna*www"
            ],
    ):
        return PayeeCategory.WORK_PERMITS
    payee = transaction.payee
    if transaction.payment_date == Day(2022, 5, 20) and "K HINGWAN VORTEX EXPENSESS" in payee:
        return PayeeCategory.WORK_PERMITS
    if transaction.payment_date == Day(2022, 11, 2) and "DUSTY KNUC" in payee:
        return PayeeCategory.WORK_PERMITS


def _maybe_rates(transaction: Transaction) -> Optional[str]:
    if matches_anywhere(transaction, ["lb hackney rates", "lbh rates"]):
        return PayeeCategory.RATES



def _maybe_electricity(transaction: Transaction) -> Optional[str]:
    if matches_anywhere(transaction, "edf energy"):
        return PayeeCategory.ELECTRICITY


def _maybe_insurance(transaction: Transaction) -> Optional[str]:
    if matches_start(
            transaction,
            [
                "close-jelf",
                "close - marshcomm",
                "axa insurance"
            ]):
        return PayeeCategory.INSURANCE


def _maybe_kashflow(transaction: Transaction) -> Optional[str]:
    if matches_anywhere(transaction, "www.kashflow.com"):
        return PayeeCategory.KASHFLOW


def _maybe_cc_fees(transaction: Transaction) -> Optional[str]:
    if matches_anywhere(transaction, "pas re cps"):
        return PayeeCategory.CREDIT_CARD_FEES


def _maybe_bb_loan(transaction: Transaction) -> Optional[str]:
    if matches_start(transaction, "loan"):
        return PayeeCategory.BB_LOAN
    if matches_anywhere(transaction, " loan"):
        return PayeeCategory.BB_LOAN


def _maybe_petty_cash(transaction: Transaction) -> Optional[str]:
    if matches_anywhere(transaction, "cash halifax"):
        return PayeeCategory.PETTY_CASH


def _maybe_bank_fees(transaction: Transaction) -> Optional[str]:
    if matches_anywhere(
            transaction,
            [
                "non-sterling transaction fee",
                "charge renewal fee",
                "total charges to",
            ]

    ):
        return PayeeCategory.BANK_FEES


def _maybe_bank_interest(transaction: Transaction) -> Optional[str]:
    if matches_anywhere(transaction, "interest to"):
        return PayeeCategory.BANK_INTEREST


def _maybe_salaries(transaction: Transaction) -> Optional[str]:
    if matches_start(
            transaction,
            [
                "pauline le divenac",
                "daniel garel",
                "kim macari",
                "tea earle",
                "ted mitchell",
            ]

    ):
        return PayeeCategory.SALARIES


def _maybe_memberships(transaction: Transaction) -> Optional[str]:
    if matches_anywhere(transaction, "stripe") and not matches_anywhere(transaction, "mushroom"):
        return PayeeCategory.MEMBERSHIPS
    if matches_anywhere(transaction, "chinekwu"):
        return PayeeCategory.MEMBERSHIPS


def _maybe_zettle_credits(transaction: Transaction) -> Optional[str]:
    if matches_anywhere(transaction, "paypal ppwdl"):
        return PayeeCategory.ZETTLE_CREDITS


def _maybe_ticketweb_credits(transaction: Transaction) -> Optional[str]:
    if "ticketweb" in transaction.payee.lower() and transaction.amount > 0:
        return PayeeCategory.TICKETWEB_CREDITS
    return None


def _maybe_bar_purchases(transaction: Transaction) -> Optional[str]:
    if matches_start(
            transaction,
            [
                "dalston local",
                "east london brew",
                "flint wines",
                "humble grape",
                "london beer gas",
                "london gases",
                "majestic wine",
                "newcomer wines",
                "sainsbury",
            ]

    ):
        return PayeeCategory.BAR_STOCK


def _maybe_security(transaction: Transaction) -> Optional[str]:
    if matches_start(transaction, "denise williams"):
        return PayeeCategory.SECURITY


def _maybe_fire_alarm(transaction: Transaction) -> Optional[str]:
    if matches_start(transaction, "agf fire prot"):
        return PayeeCategory.FIRE_ALARM


def _maybe_vat(transaction: Transaction) -> Optional[str]:
    if matches_start(transaction, "hmrc vat"):
        return PayeeCategory.VAT


def _maybe_cleaning(transaction: Transaction) -> Optional[str]:
    if matches_start(transaction, "poolfresh"):
        return PayeeCategory.CLEANING


def _maybe_piano_tuner(transaction: Transaction) -> Optional[str]:
    if matches_start(transaction, ["b sharp pianos", "dafydd james"]):
        return PayeeCategory.PIANO_TUNER


def _maybe_sound_engineer(tr: Transaction) -> Optional[str]:
    if tr.amount > 0:
        return None

    known_engineers = [
        "adrian kunstler",
        "andrew marriott",
        "bella cooper",
        "chris penty",
        "egglectic",
        "felix threadgill",
        "giulo matheson",
        "giulio matheson",
        "joe mashiter",
        "jorge martinez",
        "kinga ilyes",
        "mike omalley",
        "mike o'malley",
        "milo mcguire",
        "ochuko okiemute",
        "thomas pew",
    ]
    if matches_start(tr, known_engineers):
        return PayeeCategory.SOUND_ENGINEER


def _maybe_prs(tr: Transaction) -> Optional[str]:
    if matches_start(tr, "prs "):
        return PayeeCategory.PRS


def _maybe_mailchimp(tr: Transaction) -> Optional[str]:
    if matches_anywhere(tr, "mailchi"):
        return PayeeCategory.MAILCHIMP


def _maybe_host(tr: Transaction) -> Optional[str]:
    if matches_start(tr, "oblong"):
        return PayeeCategory.WEB_HOST


def _maybe_bt(tr: Transaction) -> Optional[str]:
    if matches_start(tr, "bt group"):
        return PayeeCategory.BT


def _maybe_slack(tr: Transaction) -> Optional[str]:
    payee = tr.payee.lower()
    if payee.startswith("int") and "slack" in payee:
        return PayeeCategory.SLACK


def _maybe_bar_snacks(tr: Transaction) -> Optional[str]:
    if matches_start(tr, "uk bar snacks"):
        return PayeeCategory.BAR_SNACKS


def _maybe_airtable(tr: Transaction) -> Optional[str]:
    payee = tr.payee.lower()
    if payee.startswith("int") and "airtable" in payee:
        return PayeeCategory.AIRTABLE


def _maybe_musician_payments(tr: Transaction) -> Optional[str]:
    payee = tr.payee.lower()
    if tr.amount < 0:
        for m in MUSICIANS:
            if payee.startswith(m):
                return PayeeCategory.MUSICIAN_PAYMENTS
            if m in payee and "new vortex jazz" in payee:
                return PayeeCategory.MUSICIAN_PAYMENTS


def _maybe_mvt(tr: Transaction) -> Optional[str]:
    if matches_start(tr, "music venue trust"):
        return PayeeCategory.MUSIC_VENUE_TRUST


def _maybe_tissues(tr: Transaction) -> Optional[str]:
    if matches_start(tr, "nisbets"):
        return PayeeCategory.TISSUES


def _maybe_telephone(tr: Transaction) -> Optional[str]:
    if matches_start(tr, "studio upstairs"):
        return PayeeCategory.TELEPHONE


def _maybe_building_maintenance(tr: Transaction) -> Optional[str]:
    if matches_start(tr, ["rentokil", "acme catering"]):
        return PayeeCategory.BUILDING_MAINTENANCE
    if matches_anywhere(tr, "locksmiths"):
        return PayeeCategory.BUILDING_MAINTENANCE


def _maybe_musician_costs(tr: Transaction) -> Optional[str]:
    if matches_anywhere(tr, ["premier cars", "kingslandlocke", "eagle mini cabs"]):
        return PayeeCategory.MUSICIAN_COSTS
    if matches_start(tr, "eurostar"):
        return PayeeCategory.MUSICIAN_COSTS


def _maybe_operational_costs(tr: Transaction) -> Optional[str]:
    if matches_start(
            tr,
            [
                "post office",
                "leyland",
                "dalston stationers",
                "www.nisbets.com",
                "lb hackney genfund"       # Hackney Council, bin collection
            ]):
        return PayeeCategory.OPERATIONAL_COSTS

    if matches_anywhere(tr, ["shopify", "amazon"]) and -50.0 < tr.amount < 0.0:
        return PayeeCategory.OPERATIONAL_COSTS


def _maybe_rent(tr: Transaction) -> Optional[str]:
    if matches_start(tr, "hcd vortex rent"):
        return PayeeCategory.RENT

def _maybe_license_renewal(tr: Transaction) -> Optional[str]:
    if matches_start(tr, "hackney.gov.uk"):
        return PayeeCategory.LICENSING_DIRECT

def _maybe_building_security(tr: Transaction) -> Optional[str]:
    if matches_start(tr, ["adt inv", "adt fire"]):
        return PayeeCategory.BUILDING_SECURITY

def _maybe_space_hire(tr: Transaction) -> Optional[str]:
    if matches_start(tr, "cheng xie"):
        return PayeeCategory.SPACE_HIRE
    if matches_anywhere(tr, "mushroom") and matches_anywhere(tr, "stripe"):
        return PayeeCategory.SPACE_HIRE

def _maybe_subscriptions(tr: Transaction) -> Optional[str]:
    if matches_start(tr, ["music venues allia wimborne", "jazz in london vortex"]):
        return PayeeCategory.SUBSCRIPTIONS

def category_for_transaction(transaction: Transaction) -> Optional[PayeeCategory]:
    return (_maybe_airtable(transaction) or
            _maybe_bank_fees(transaction) or
            _maybe_bank_interest(transaction) or
            _maybe_bar_purchases(transaction) or
            _maybe_bar_snacks(transaction) or
            _maybe_bb_loan(transaction) or
            _maybe_bt(transaction) or
            _maybe_building_maintenance(transaction) or
            _maybe_building_security(transaction) or
            _maybe_cc_fees(transaction) or
            _maybe_cleaning(transaction) or
            _maybe_electricity(transaction) or
            _maybe_fire_alarm(transaction) or
            _maybe_host(transaction) or
            _maybe_insurance(transaction) or
            _maybe_kashflow(transaction) or
            _maybe_license_renewal(transaction) or
            _maybe_mailchimp(transaction) or
            _maybe_memberships(transaction) or
            _maybe_musician_costs(transaction) or
            _maybe_musician_payments(transaction) or
            _maybe_mvt(transaction) or
            _maybe_operational_costs(transaction) or
            _maybe_petty_cash(transaction) or
            _maybe_piano_tuner(transaction) or
            _maybe_prs(transaction) or
            _maybe_rates(transaction) or
            _maybe_rent(transaction) or
            _maybe_salaries(transaction) or
            _maybe_security(transaction) or
            _maybe_slack(transaction) or
            _maybe_sound_engineer(transaction) or
            _maybe_space_hire(transaction) or
            _maybe_subscriptions(transaction) or
            _maybe_telephone(transaction) or
            _maybe_ticketweb_credits(transaction) or
            _maybe_tissues(transaction) or
            _maybe_vat(transaction) or
            _maybe_work_permit(transaction) or
            _maybe_zettle_credits(transaction)
            )
