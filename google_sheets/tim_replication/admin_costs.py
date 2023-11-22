from numbers import Number
from typing import List

from airtable_db.contracts_and_events import GigsInfo
from bank_statements import BankActivity
from bank_statements.payee_categories import PayeeCategory
from date_range import DateRange
from google_sheets.tab_range import TabCell
from google_sheets.tim_replication.accounts_range import AccountsRange
from google_sheets.tim_replication.constants import QUARTERLY_RENT, QUARTERLY_RENTOKILL, QUARTERLY_WASTE_COLLECTION, \
    QUARTERLY_BIN_HIRE_EX_VAT, YEARLY_DOOR_SECURITY, MONTHLY_FOWLERS_ALARM
from kashflow.nominal_ledger import NominalLedger, NominalLedgerItemType
from utils import checked_type


class AdminCostsRange(AccountsRange):
    NUM_ROWS = 29

    (TITLE, _, SUB_PERIOD, TOTAL,
     RENT,
     RATES,
     ELECTRICITY,
     TELEPHONE,
     INSURANCE,
     SALARIES,
     RENTOKIL,
     WASTE_COLLECTION,
     BIN_HIRE,
     CONSOLIDATED_DOOR_SECURITY,
     FOWLERS_ALARM,
     DAILY_CLEANING,
     BUILDING_MAINTENANCE,
     BUILDING_WORKS,
     DOWNSTAIRS_BUILDING_WORKS,
     PIANO_TUNING,
     EQUIPMENT_PURCHASE,
     EQUIPMENT_MAINTENANCE,
     KASHFLOW,
     OPERATIONAL_COSTS,
     LICENSING_INDIRECT,
     CREDIT_CARD_FEES,
     BB_LOAN,
     BANK_FEES,
     BANK_INTEREST) = range(NUM_ROWS)

    def __init__(
            self,
            top_left_cell: TabCell,
            sub_periods: List[DateRange],
            sub_period_titles: List[any],
            gigs_info: GigsInfo,
            nominal_ledger: NominalLedger,
            bank_activity: BankActivity,
            vat_rate: float,
    ):
        super().__init__(top_left_cell, self.NUM_ROWS, sub_periods, sub_period_titles, gigs_info, nominal_ledger,
                         bank_activity)
        self.bank_activities_by_sub_period: List[BankActivity] = [bank_activity.restrict_to_period(sub_period) for
                                                                  sub_period in sub_periods]
        self.vat_rate: float = checked_type(vat_rate, Number)

    def format_requests(self):
        return super().common_requests() + [
            self.tab.group_rows_request(self.i_first_row + self.RENT,
                                        self.i_first_row + self.BANK_INTEREST),
        ]

    def values(self):
        values = self.sub_period_values()
        values += [(
            self[:, 0],
            ["Admin", "", "Period", "Total", "Rent", "Rates", "Electricity", "Telephone",
             "Insurance",
             "Salaries", "Rentokil", "Waste Collection", "Bin Hire",
             "Consolidated Door Security", "Alarm (Fowler's)", "Cleaning", "Building Maintenance",
             "Building Works", "Downstairs Building Works", "Piano Tuning", "Equipment Purchase",
             "Equipment Maintenance", "Kashflow", "Operational Costs", "Licensing - Indirect",
             "Credit Card Fees", "BB Loan Payment", "Bank Fees", "Bank Interest"]
        ), (
            self[self.TOTAL, 1:-1],
            [
                f"={self.sum_formula(self.RENT, self.BANK_INTEREST, i_col)}"
                for i_col in range(1, self.num_sub_periods + 1)
            ]
        ),
        ]

        values += [
            (self[self.RENT, 1:-1], [-QUARTERLY_RENT / 3.0 for _ in range(12)]),
            (self[self.RENTOKIL, 1:-1], [-QUARTERLY_RENTOKILL / 3.0 for _ in range(12)]),
            (self[self.WASTE_COLLECTION, 1:-1], [-QUARTERLY_WASTE_COLLECTION / 3.0 for _ in range(12)]),
            (self[self.BIN_HIRE, 1:-1], [-QUARTERLY_BIN_HIRE_EX_VAT / 3.0 for _ in range(12)]),
            (self[self.CONSOLIDATED_DOOR_SECURITY, 1:-1], [-YEARLY_DOOR_SECURITY / 12.0 for _ in range(12)]),
            (self[self.FOWLERS_ALARM, 1:-1], [-MONTHLY_FOWLERS_ALARM for _ in range(12)]),
        ]

        for (field, ledger_item) in [
            (self.TELEPHONE, NominalLedgerItemType.TELEPHONE),
            (self.SALARIES, NominalLedgerItemType.STAFF_COSTS),
            (self.DAILY_CLEANING, NominalLedgerItemType.CLEANING),
            (self.BUILDING_MAINTENANCE, NominalLedgerItemType.BUILDING_MAINTENANCE),
            (self.BUILDING_WORKS, NominalLedgerItemType.BUILDING_WORKS),
            (self.DOWNSTAIRS_BUILDING_WORKS, NominalLedgerItemType.DOWNSTAIRS_BUILDING_WORKS),
            (self.PIANO_TUNING, NominalLedgerItemType.PIANO_TUNING),
            (self.EQUIPMENT_PURCHASE, NominalLedgerItemType.EQUIPMENT_PURCHASE),
            (self.EQUIPMENT_MAINTENANCE, NominalLedgerItemType.EQUIPMENT_MAINTENANCE),
            (self.OPERATIONAL_COSTS, NominalLedgerItemType.OPERATIONAL_COSTS),
            (self.LICENSING_INDIRECT, NominalLedgerItemType.LICENSING_INDIRECT),
        ]:
            values.append(
                (self[field, 1:-1], [ledger.total_for(ledger_item) for ledger in self.ledger_by_sub_period])
            )

        for (field, category, subtract_vat) in [
            (self.RATES, PayeeCategory.RATES, False),
            (self.ELECTRICITY, PayeeCategory.ELECTRICITY, True),
            (self.INSURANCE, PayeeCategory.INSURANCE, False),
            (self.KASHFLOW, PayeeCategory.KASHFLOW, True),
            (self.CREDIT_CARD_FEES, PayeeCategory.CREDIT_CARD_FEES, False),
            (self.BB_LOAN, PayeeCategory.BB_LOAN, False),
            (self.BANK_FEES, PayeeCategory.BANK_FEES, False),
            (self.BANK_INTEREST, PayeeCategory.BANK_INTEREST, False),
        ]:
            vat_adjustment = 1.2 if subtract_vat else 1.0
            values.append(
                (self[field, 1:-1],
                 [activity.net_amount_for_category(category) / vat_adjustment
                  for activity in self.bank_activity_by_sub_period])
            )

        # To date values
        values += [
            (
                self[i_row, -1],
                f"=SUM({self[i_row, 1:self.num_sub_periods + 1].in_a1_notation})"
            )
            for i_row in range(self.TOTAL, self.BANK_INTEREST + 1)

        ]

        return values
