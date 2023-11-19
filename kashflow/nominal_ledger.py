from numbers import Number
from pathlib import Path
from typing import List

from date_range import Day, DateRange
from env import KASHFLOW_CSV_DIR
from utils import checked_list_type, checked_type
from utils.file_utils import read_csv_file
from utils.logging import log_message


class NominalLedgerItemType:
    BAR_STOCK = "Bar Stock"
    BUILDING_MAINTENANCE = "Building Maintenance"
    BUILDING_WORKS = "Building works"
    CLEANING = "Cleaning"
    DOWNSTAIRS_BUILDING_WORKS = "Downstairs building works"
    EQUIPMENT_MAINTENANCE = "Equipment Maintenance"
    EQUIPMENT_PURCHASE = "Equipment Purchases"
    LICENSING_INDIRECT = "Licensing - Indirect"
    MARKETING = "Marketing - Indirect"
    OPERATIONAL_COSTS = "Operational Costs"
    OUTPUT_VAT = "Output VAT"
    PIANO_TUNING = "Piano tuning"
    SECURITY = "Door Security"
    SOUND_ENGINEERING = "Sound engineering"
    SPACE_HIRE = "Space Hire"
    STAFF_COSTS = "Staff Costs"
    TELEPHONE = "Telephone"


class NominalLedgerItem:
    def __init__(
            self,
            code: int,
            item_type: str,
            date: Day,
            reference: str,
            narrative: str,
            amount: float,
    ):
        self.code: int = checked_type(code, int)
        self.item_type: str = checked_type(item_type, str).strip()
        self.date: Day = checked_type(date, Day)
        self.reference: str = checked_type(reference, str)
        self.narrative: str = checked_type(narrative, str)
        self.amount: float = checked_type(amount, float)


class NominalLedger:
    def __init__(self, ledger_items: List[NominalLedgerItem]):
        self.ledger_items = checked_list_type(ledger_items, NominalLedgerItem)

    def restrict_to_period(self, period: DateRange) -> 'NominalLedger':
        return NominalLedger([item for item in self.ledger_items if period.contains_day(item.date)])

    def filter_on_item_type(self, item_type: str) -> 'NominalLedger':
        return NominalLedger([item for item in self.ledger_items if item.item_type.upper() == item_type.upper()])

    def total_amount(self) -> float:
        return sum(item.amount for item in self.ledger_items)

    def total_for(self, item_type: str) -> float:
        return self.filter_on_item_type(item_type).total_amount()

    @property
    def total_space_hire(self) -> float:
        return self.total_for(NominalLedgerItemType.SPACE_HIRE)

    @property
    def bar_stock(self) -> float:
        return self.total_for(NominalLedgerItemType.BAR_STOCK)

    @property
    def sound_engineering(self) -> float:
        return self.total_for(NominalLedgerItemType.SOUND_ENGINEERING)

    @property
    def security(self) -> float:
        return self.total_for(NominalLedgerItemType.SECURITY)

    @property
    def marketing(self) -> float:
        return self.total_for(NominalLedgerItemType.MARKETING)

    @staticmethod
    def from_csv_file(file: Path = None):
        file = file or NominalLedger.latest_csv_file()

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

        def to_float(text: str) -> Number:
            return float(text.replace(",", ""))

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
                        amount = 0.0
                    else:
                        amount = to_float(row[6])
                else:
                    amount = -to_float(row[5])
                ledger_items.append(NominalLedgerItem(
                    code=code,
                    item_type=item_type,
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
    def latest_csv_file() -> Path:
        files = list(KASHFLOW_CSV_DIR.glob('*.csv'))
        assert len(files) > 0, f"No kashflow files found in {KASHFLOW_CSV_DIR}"
        files = sorted(files, key=lambda f: f.stat().st_mtime)
        return files[-1]

    @staticmethod
    def empty():
        return NominalLedger([])