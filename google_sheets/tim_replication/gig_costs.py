from numbers import Number
from typing import List

from airtable_db.contracts_and_events import GigsInfo
from airtable_db.table_columns import TicketPriceLevel
from date_range import DateRange
from google_sheets.tab_range import TabCell
from google_sheets.tim_replication.accounts_range import AccountsRange
from kashflow.nominal_ledger import NominalLedger, NominalLedgerItemType
from utils import checked_type


class GigCostsRange(AccountsRange):
    NUM_ROWS = 14

    (TITLE, _, SUB_PERIOD, TOTAL, MUSICIAN_FEES, OTHER_COSTS, ACCOMMODATION, TRAVEL, CATERING, EQUIPMENT,
     WORK_PERMITS,
     SECURITY,
     SOUND_ENGINEERING, MARKETING) = range(NUM_ROWS)

    def __init__(
            self,
            top_left_cell: TabCell,
            sub_periods: List[DateRange],
            sub_period_titles: List[any],
            gigs_info: GigsInfo,
            nominal_ledger: NominalLedger,
            vat_rate: float,
    ):
        super().__init__(top_left_cell, self.NUM_ROWS, sub_periods, sub_period_titles, gigs_info, nominal_ledger)
        self.vat_rate: float = checked_type(vat_rate, Number)

    def format_requests(self):
        return super().common_requests() + [
            self.tab.group_rows_request(self.i_first_row + self.ACCOMMODATION,
                                        self.i_first_row + self.WORK_PERMITS),
            self.tab.group_rows_request(self.i_first_row + self.MUSICIAN_FEES,
                                        self.i_first_row + self.MARKETING),
            # self[self.OTHER_COSTS].border_request(["top"]),
            # self[self.WORK_PERMITS].border_request(["bottom"]),
            self[self.ACCOMMODATION:self.WORK_PERMITS + 1, 0].right_align_text_request(),
        ]

    def values(self):
        values = self.sub_period_values()
        values += [(
            self[:, 0],
            ["Gig Costs", "", "Period", "Total", "Fees", "Other Costs", "Accommodation", "Travel", "Catering",
             "Equipment", "Work Permits", "Security", "Sound Engineer", "Marketing"]
        ), (
            self[self.TOTAL, 1:-1],
            [
                f"={self.sum_formula(self.MUSICIAN_FEES, self.OTHER_COSTS, i_col)} + {self.sum_formula(self.SECURITY, self.MARKETING, i_col)}"
                for i_col in range(1, self.num_sub_periods + 1)
            ]
        ), (
            self[self.OTHER_COSTS, 1:-1],
            [
                f"={self.sum_formula(self.ACCOMMODATION, self.WORK_PERMITS, i_col)}"
                for i_col in range(1, self.num_sub_periods + 1)
            ]
        )
        ]

        for (field, func) in [
            (self.MUSICIAN_FEES, lambda gig: -gig.musicians_fees),
            (self.ACCOMMODATION, lambda gig: -gig.band_accommodation),
            (self.TRAVEL, lambda gig: -gig.band_transport),
            (self.CATERING, lambda gig: -gig.band_catering / 1.2),
        ]:
            values.append(
                (self[field, 1:-1], [func(gig) for gig in self.gigs_by_sub_period])
            )

        for (field, func) in [
            (self.SOUND_ENGINEERING, lambda ledger: ledger.sound_engineering),
            (self.SECURITY, lambda ledger: ledger.security),
            (self.MARKETING, lambda ledger: ledger.marketing),
        ]:
            values.append(
                (self[field, 1:-1], [func(ledger) for ledger in self.ledger_by_sub_period])
            )

        # To date values
        values += [
            (
                self[i_row, -1],
                f"=SUM({self[i_row, 1:self.num_sub_periods + 1].in_a1_notation})"
            )
            for i_row in range(self.TOTAL, self.MARKETING + 1)

        ]

        return values
