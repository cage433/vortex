from enum import StrEnum, verify, UNIQUE
from pathlib import Path

from vortex.utils import checked_type


def _musicians():
    file = Path(__file__).parent.parent.parent / "resources" / "musicians.txt"
    musicians = []
    with open(file) as f:
        for line in f.readlines():
            musicians.append(line.strip())
    return musicians


MUSICIANS = _musicians()

class PayeeCategoryClass(StrEnum):
    FINANCE = "Finance"
    OPERATIONAL = "Operational"
    UTILITIES = "Utilities"
    TICKETS = "Tickets"
    EQUIPMENT = "Equipment"
    SOUND_ENGINEERS = "Sound Engineers"


@verify(UNIQUE)
class PayeeCategory(StrEnum):
    ACCOUNTANT = "Accountant"
    AIRTABLE = "Airtable"
    BANK_FEES = "Bank Fees"
    BANK_INTEREST = "Bank Interest"
    BAR_STOCK = "Bar Stock"
    BAR_SNACKS = "Bar Snacks"
    BB_LOAN = "BB Loan"
    BT = "BT"
    BUILDING_MAINTENANCE = "Building Maintenance"
    BUILDING_SECURITY = "Building Security"
    BUILDING_WORKS = "Building Works"
    CARD_SALES = "Card Sales"
    CASH_SALES = "Cash Sales"
    CLEANING = "Cleaning"
    CREDIT_CARD_FEES = "Credit Card Fees"
    DIRECTORS_LOAN = "Directors Loan"
    DONATION = "Donation"
    ELECTRICITY = "Electricity"
    EQUIPMENT_HIRE = "Equipment Hire"
    EQUIPMENT_MAINTENANCE = "Equipment Maintenance"
    EQUIPMENT_PURCHASE = "Equipment Purchase"
    FIRE_ALARM = "Fire Alarm"
    FLOOD = "Flood"
    GIG_SECURITY = "Gig Security"
    GRANT = "Grant"
    INSURANCE = "Insurance"
    INSURANCE_PAYOUT = "Insurance Payout"
    INTERNAL_TRANSFER = "Internal Transfer"
    KASHFLOW = "Kashflow"
    MAILCHIMP = "Mailchimp"
    LICENSING = "Licensing"
    MARKETING = "Marketing Direct"
    MEMBERSHIPS = "Memberships"
    MUSICIAN_COSTS = "Musician Costs"
    MUSICIAN_PAYMENTS = "Musician Payments"
    MUSIC_VENUE_TRUST = "Music Venue Trust"
    OPERATIONAL_COSTS = "Operational Costs"
    PETTY_CASH = "Petty Cash"
    PIANO_TUNER = "Piano Tuner"
    PRS = "PRS"
    RATES = "Rates"
    RENT = "Rent"
    SALARIES = "Salaries"
    SLACK = "Slack"
    SOUND_ENGINEER = "Sound Engineer"
    SPACE_HIRE = "Space Hire"
    SUBSCRIPTIONS = "Subscriptions"
    TELEPHONE = "Telephone"
    THAMES_WATER = "Thames Water"
    TICKET_SALES = "Ticketweb Credits"
    UNCATEGORISED = "Uncategorised"
    UTILITIES = "Utilities"
    VAT = "VAT"
    VORTEX_MERCH = "Vortex Merch"
    WEB_HOST = "Web Host"
    WORK_PERMITS = "Work Permits"

    @staticmethod
    def is_subject_to_vat(category: 'PayeeCategory') -> bool:
        if category in [
            PayeeCategory.BANK_FEES,
            PayeeCategory.BB_LOAN,
            PayeeCategory.BANK_INTEREST,
            PayeeCategory.CREDIT_CARD_FEES,
            PayeeCategory.DONATION,
            PayeeCategory.GIG_SECURITY,
            PayeeCategory.GRANT,
            PayeeCategory.INSURANCE_PAYOUT,
            PayeeCategory.INTERNAL_TRANSFER,
            PayeeCategory.MEMBERSHIPS,
            PayeeCategory.MUSIC_VENUE_TRUST,
            PayeeCategory.MUSICIAN_PAYMENTS,
            PayeeCategory.PETTY_CASH,
            PayeeCategory.PIANO_TUNER,
            PayeeCategory.RATES,
            PayeeCategory.SALARIES,
            PayeeCategory.SOUND_ENGINEER,
            PayeeCategory.TICKET_SALES,
            PayeeCategory.UNCATEGORISED,
            PayeeCategory.VAT,
            PayeeCategory.VORTEX_MERCH,
            PayeeCategory.WORK_PERMITS
        ]:
            return False

        if category in [
            PayeeCategory.ACCOUNTANT,
            PayeeCategory.AIRTABLE,
            PayeeCategory.BAR_SNACKS,
            PayeeCategory.BAR_STOCK,
            PayeeCategory.BT,
            PayeeCategory.BUILDING_MAINTENANCE,
            PayeeCategory.BUILDING_SECURITY,
            PayeeCategory.BUILDING_WORKS,
            PayeeCategory.CARD_SALES,
            PayeeCategory.CLEANING,
            PayeeCategory.ELECTRICITY,
            PayeeCategory.EQUIPMENT_HIRE,
            PayeeCategory.EQUIPMENT_MAINTENANCE,
            PayeeCategory.EQUIPMENT_PURCHASE,
            PayeeCategory.FIRE_ALARM,
            PayeeCategory.FLOOD,
            PayeeCategory.INSURANCE,
            PayeeCategory.KASHFLOW,
            PayeeCategory.LICENSING,
            PayeeCategory.MAILCHIMP,
            PayeeCategory.MARKETING,
            PayeeCategory.MUSICIAN_COSTS,
            PayeeCategory.OPERATIONAL_COSTS,
            PayeeCategory.PRS,
            PayeeCategory.RENT,
            PayeeCategory.SLACK,
            PayeeCategory.SPACE_HIRE,
            PayeeCategory.SUBSCRIPTIONS,
            PayeeCategory.TELEPHONE,
            PayeeCategory.THAMES_WATER,
            PayeeCategory.UTILITIES,
            PayeeCategory.WEB_HOST,
        ]:
            return True

        raise ValueError(f"Unknown category for VAT [{category}]")

    @staticmethod
    def is_credit(category: 'PayeeCategory') -> bool:
        checked_type(category, PayeeCategory)
        return category in [
            PayeeCategory.CARD_SALES,
            PayeeCategory.CASH_SALES,
            PayeeCategory.TICKET_SALES,
            PayeeCategory.SPACE_HIRE,
            PayeeCategory.MEMBERSHIPS,
            PayeeCategory.INSURANCE_PAYOUT
        ]

    @staticmethod
    def is_debit(category: 'PayeeCategory') -> bool:
        checked_type(category, PayeeCategory)
        return not PayeeCategory.is_credit(category)

