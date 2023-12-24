from abc import ABC, abstractmethod
from numbers import Number

from airtable_db.contracts_and_events import GigsInfo
from date_range.month import Month
from google_sheets.tab_range import TabRange, TabCell
from kashflow.nominal_ledger import NominalLedger
from utils import checked_type


class VortexSummaryRange(TabRange, ABC):
    def __init__(self, top_left_cell: TabCell, gigs_info: GigsInfo, title: str):
        self.first_year = gigs_info.first_day.y
        self.last_year = gigs_info.last_day.y
        self.num_years = self.last_year - self.first_year + 1
        super().__init__(top_left_cell, 2 + self.num_years, 14)
        self.title: str = checked_type(title, str)

    @abstractmethod
    def value_for_month(self, month: Month) -> Number:
        pass

    def format_requests(self):
        return [
            self.outline_border_request(),
            self[0].merge_columns_request(),
            self[0].center_text_request(),
            self[0:2].set_bold_text_request(),
            self[1].border_request(["bottom"]),
            self[:, 0].set_bold_text_request(),
            self[1:, 0].border_request(["right"]),
            self[1].right_align_text_request(),
            self[1:, 1:].set_decimal_format_request("#,##0"),
        ]

    def values(self):
        values = [
            (self[0, 0], self.title),
            (self[1], ["Year", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct",
                       "Nov", "Dec", "Total"]),
        ]
        for year in range(self.first_year, self.last_year + 1):
            values.append(
                (self[2 + year - self.first_year, 1:13],

                 [
                     self.value_for_month(Month(year, month))
                     for month in range(1, 13)]
                 )
            )
        values.append((self[2:self.num_years + 2, 0], list(range(self.first_year, self.last_year + 1))))
        for i_row in range(2, self.num_years + 2):
            period_range = self[i_row, 1:13]
            values.append(
                (self[i_row, -1], f"=Sum({period_range.in_a1_notation})")
            )
        return values


class AudienceRange(VortexSummaryRange):
    def __init__(self, top_left_cell: TabCell, gigs_info: GigsInfo):
        super().__init__(top_left_cell, gigs_info, "Audience")
        self.gigs_info: GigsInfo = checked_type(gigs_info, GigsInfo)

    def value_for_month(self, month: Month) -> Number:
        return self.gigs_info.restrict_to_period(month).total_tickets


class TicketSalesRange(VortexSummaryRange):
    def __init__(self, top_left_cell: TabCell, gigs_info: GigsInfo):
        super().__init__(top_left_cell, gigs_info, "Ticket Sales")
        self.gigs_info: GigsInfo = checked_type(gigs_info, GigsInfo)

    def value_for_month(self, month: Month) -> Number:
        return self.gigs_info.restrict_to_period(month).total_ticket_sales


class BarTakingsRange(VortexSummaryRange):
    VAT_RATE = 0.2

    def __init__(self, top_left_cell: TabCell, gigs_info: GigsInfo):
        super().__init__(top_left_cell, gigs_info, "Bar Sales")
        self.gigs_info: GigsInfo = checked_type(gigs_info, GigsInfo)

    def value_for_month(self, month: Month) -> Number:
        return self.gigs_info.restrict_to_period(month).bar_takings / (1 + self.VAT_RATE)


class BarProfitRange(VortexSummaryRange):
    VAT_RATE = 0.2

    def __init__(self, top_left_cell: TabCell, gigs_info: GigsInfo, nominal_ledger: NominalLedger):
        super().__init__(top_left_cell, gigs_info, "Bar Profit")
        self.gigs_info: GigsInfo = checked_type(gigs_info, GigsInfo)
        self.nominal_ledger: NominalLedger = checked_type(nominal_ledger, NominalLedger)

    def value_for_month(self, month: Month) -> Number:
        restricted_gigs = self.gigs_info.restrict_to_period(month)
        takings = restricted_gigs.bar_takings / (1 + self.VAT_RATE)
        evening_purchases = -restricted_gigs.evening_purchases / (1 + self.VAT_RATE)
        restricted_ledger = self.nominal_ledger.restrict_to_period(month)
        delivered_purchases = restricted_ledger.bar_stock

        return takings + evening_purchases + delivered_purchases


class RehearsalAndHireFeesRange(VortexSummaryRange):
    VAT_RATE = 0.2

    def __init__(self, top_left_cell: TabCell, gigs_info: GigsInfo, nominal_ledger: NominalLedger):
        super().__init__(top_left_cell, gigs_info, "Rehearsal and hire fees (excluding gigs)")
        self.gigs_info: GigsInfo = checked_type(gigs_info, GigsInfo)
        self.nominal_ledger: NominalLedger = checked_type(nominal_ledger, NominalLedger)

    def value_for_month(self, month: Month) -> Number:
        restricted_gigs = self.gigs_info.restrict_to_period(month)
        restricted_ledger = self.nominal_ledger.restrict_to_period(month)
        evening_hire = restricted_gigs.excluding_hires.hire_fees / (1 + self.VAT_RATE)
        day_hire = restricted_ledger.total_space_hire

        return evening_hire + day_hire
