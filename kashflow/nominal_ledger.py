import shelve
from decimal import Decimal
from enum import Enum
from numbers import Number
from pathlib import Path
from typing import List, Optional

from date_range import Day, DateRange
from date_range.accounting_year import AccountingYear
from env import KASHFLOW_CSV_DIR
from utils import checked_list_type, checked_type, checked_optional_type
from utils.file_utils import read_csv_file
from utils.logging import log_message


class NominalLedgerItemType(Enum):
    ADMINISTRATION = "Administration"
    BAR_STOCK = "Bar Stock"
    BUILDING_MAINTENANCE = "Building Maintenance"
    BUILDING_SECURITY = "Building Security"
    BUILDING_WORKS = "Building Works"
    CLEANING = "Cleaning"
    DONATIONS = "Donations"
    DOWNSTAIRS_BUILDING_WORKS = "Downstairs Building Works"
    DRINKS = "Drinks"
    ELECTRICITY = "Electricity"
    EQUIPMENT_HIRE = "Equipment Hire"
    EQUIPMENT_MAINTENANCE = "Equipment Maintenance"
    EQUIPMENT_PURCHASE = "Equipment Purchases"
    FLOOD_CLEARANCE = "Flood Clearance"
    Grants = "Grants"
    INPUT_VAT = "Input VAT"
    INSURANCE = "Insurance"
    LICENSING_INDIRECT = "Licensing - Indirect"
    LICENSING_DIRECT = "Licensing -Direct"
    LOAN_REPAYMENT = "Loan Repayment"
    MARKETING_INDIRECT = "Marketing - Indirect"
    MARKETING_DIRECT = "Marketing - Direct"
    MUSICIAN_COSTS = "Musician Costs"
    MUSICIANS_FEES = "Musicians Fees"
    OPERATIONAL_COSTS = "Operational Costs"
    OTHER = "Other"
    OUTPUT_VAT = "Output VAT"
    PIANO_TUNING = "Piano Tuning"
    PROJECTS = "Projects"
    RATES = "Rates"
    RENT = "Rent & Service Charge"
    SECURITY = "Door Security"
    SERVICES = "Services"
    SOUND_ENGINEERING = "Sound engineering"
    SPACE_HIRE = "Space Hire"
    STAFF_COSTS = "Staff Costs"
    SUBSCRIPTIONS = "Subscriptions"
    TELEPHONE = "Telephone"
    TICKETS = "Tickets"
    TRAVEL = "Travel"
    UTILITIES = "Utilities"
    VOLUNTEER_COSTS = "Volunteer Costs"
    VORTEX_JAZZ_FESTIVAL = "Vortex Jazz Festival"
    WORK_PERMITS = "Work Permits"

    @staticmethod
    def from_text(text: str):
        if text == "Piano tuning":
            text = "Piano Tuning"
        if text.lower() == "downstairs building works":
            text = "Downstairs Building Works"
        if text.lower() == "building works":
            text = "Building Works"
        if text.lower() == "flood clearance":
            text = "Flood Clearance"
        if text.lower() == "projects & events":
            text = "Projects"
        return NominalLedgerItemType(text)

class NominalLedgerItem:
    def __init__(
            self,
            code: int,
            item_type: NominalLedgerItemType,
            date: Day,
            reference: str,
            narrative: str,
            amount: Decimal,
    ):
        self.code: int = checked_type(code, int)
        self.item_type: str = checked_type(item_type, NominalLedgerItemType)
        self.date: Day = checked_type(date, Day)
        self.reference: str = checked_type(reference, str)
        self.narrative: str = checked_type(narrative, str)
        self.amount: Decimal = checked_type(amount, Decimal)

    def __str__(self):
        return f"{self.date}: {self.amount}, {self.reference}, {self.item_type}"


class NominalLedger:
    def __init__(self, ledger_items: List[NominalLedgerItem]):
        self.ledger_items = checked_list_type(ledger_items, NominalLedgerItem)

    def restrict_to_period(self, period: DateRange) -> 'NominalLedger':
        return NominalLedger([item for item in self.ledger_items if period.contains_day(item.date)])

    def filter_on_item_type(self, item_type: NominalLedgerItemType) -> 'NominalLedger':
        return NominalLedger([item for item in self.ledger_items if item.item_type == item_type])

    def total_amount(self) -> Decimal:
        return sum(item.amount for item in self.ledger_items)

    def total_for(self, item_type: NominalLedgerItemType) -> Decimal:
        return self.filter_on_item_type(item_type).total_amount()

    @property
    def item_types(self) -> List[NominalLedgerItemType]:
        return list(set(item.item_type for item in self.ledger_items))

    SHELF = Path(__file__).parent / "_nominal_ledger.shelf"

    @staticmethod
    def _from_csv_file(file: Path) -> 'NominalLedger':
        def ignore_row(row: List[any]):
            if len(row) <= 6:
                return True
            if row[0] == "" and row[4] == "TOTALS":
                return True
            if row[0] == "" and row[4] == "BALANCE":
                return True
            if all([r == "" for r in row]):
                return True

            return False

        def to_decimal(text: str) -> Decimal:
            return Decimal(text.replace(",", ""))

        rows = read_csv_file(file)
        while rows[0][0] != "CODE":
            rows.pop(0)
        rows.pop(0)
        ledger_items = []
        i = 4
        for row in rows[:-1]:
            if ignore_row(row):
                continue
            try:
                i += 1
                code = int(row[0])
                item_type = row[1].strip()
                date = Day.parse(row[2])
                reference = row[3].strip()
                narrative = row[4].strip()
                if row[5].strip() == "":
                    if row[6].strip() == "":
                        log_message(f"No amount in row {i}, {row}")
                        amount = Decimal(0.0)
                    else:
                        amount = to_decimal(row[6])
                else:
                    amount = -to_decimal(row[5])
                ledger_items.append(NominalLedgerItem(
                    code=code,
                    item_type=NominalLedgerItemType.from_text(item_type),
                    date=date,
                    reference=reference,
                    narrative=narrative,
                    amount=amount
                ))
            except Exception as e:
                print(f"Error on row, {i}: {row}")
                raise e
        return NominalLedger(ledger_items)

    @staticmethod
    def from_latest_csv_file(force: bool) -> 'NominalLedger':
        file = NominalLedger.latest_csv_file()
        key = f"nominal_ledger {file}"
        with shelve.open(str(NominalLedger.SHELF)) as shelf:
            if key not in shelf or force:
                shelf[key] = NominalLedger._from_csv_file(file)
            return shelf[key]

    @staticmethod
    def latest_csv_file() -> Path:
        files = list(KASHFLOW_CSV_DIR.glob('*.csv'))
        assert len(files) > 0, f"No kashflow files found in {KASHFLOW_CSV_DIR}"
        files = sorted(files, key=lambda f: f.stat().st_mtime)
        return files[-1]

    @staticmethod
    def empty():
        return NominalLedger([])

class NominalLedgerWithVATItem:
    def __init__(self, item: NominalLedgerItem, vat: Optional[NominalLedgerItem]):
        self.item: NominalLedgerItem = checked_type(item, NominalLedgerItem)
        self.vat: Optional[NominalLedgerItem] = checked_optional_type(vat, NominalLedgerItem)



if __name__ == '__main__':
    ledger = NominalLedger.from_latest_csv_file(force=False).restrict_to_period(AccountingYear(2024))
    for item in ledger.item_types:
        print(f"{item}: {ledger.total_for(item)}")
    print("\n\n")
