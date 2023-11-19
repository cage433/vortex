from numbers import Number
from typing import Callable

from airtable_db import VortexDB
from airtable_db.contracts_and_events import GigsInfo
from airtable_db.table_columns import TicketPriceLevel, TicketCategory
from date_range.accounting_month import AccountingMonth
from date_range.accounting_year import AccountingYear
from date_range.week import Week
from env import TEST_SHEET_ID
from google_sheets import Workbook, Tab
from google_sheets.tab_range import TabRange, TabCell
from google_sheets.tim_replication.audience_numbers_range import AudienceNumbersRange
from utils import checked_type


class MonthHeadingsRange(TabRange):
    NUM_ROWS = 3
    MONTH, START_DATE, VAT_RATE = range(NUM_ROWS)

    def __init__(self, top_left_cell: TabCell, month: AccountingMonth, vat_rate: Number):
        super().__init__(top_left_cell, num_rows=self.NUM_ROWS, num_cols=2)
        self.month = checked_type(month, AccountingMonth)
        self.vat_rate: float = checked_type(vat_rate, Number)

    def format_requests(self):
        return [
            self.outline_border_request(),
            self[self.MONTH, 1].date_format_request("mmm-yy"),
            self[self.START_DATE, 1].date_format_request("d mmm yy"),
            self[self.VAT_RATE, 1].percentage_format_request(),
            self[:, 0].set_bold_text_request(),
        ]

    def values(self) -> list[tuple[TabRange, list[list[any]]]]:
        return [
            (self[:, 0], ["Month", "Start Date", "VAT Rate"]),
            (self[:, 1], [self.month.corresponding_calendar_month.first_day, self.month.first_day, self.vat_rate]),
        ]

    @property
    def vat_cell(self):
        return self[self.VAT_RATE, -1]


class MonthAccountsRange(TabRange):
    def __init__(self, top_left_cell: TabCell, num_rows: int, num_cols: int, month: AccountingMonth,
                 gigs_info: GigsInfo):
        super().__init__(top_left_cell, num_rows, num_cols)
        self.month: AccountingMonth = checked_type(month, AccountingMonth)
        self.gigs_info: GigsInfo = checked_type(gigs_info, GigsInfo)
        self.weeks: list[Week] = month.weeks
        self.num_weeks: int = len(self.weeks)
        self.gigs_by_week: list[GigsInfo] = [self.gigs_info.restrict_to_period(w) for w in self.weeks]

    def week_gigs_row(self, gig_func: Callable[[GigsInfo], int]) -> list[any]:
        return [gig_func(gigs) for gigs in self.gigs_by_week]


class IncomeRange(MonthAccountsRange):
    NUM_ROWS = 14

    TITLE, _, WEEK, TICKET_SALES, FULL, MEMBER, CONCS, OTHER, HIRE_FEES, BAR_TAKINGS, \
        Z_READING, CC_DOOR_TICKETS, CC_ARTIST_MERCH, TOTAL = range(NUM_ROWS)

    def __init__(
            self,
            top_left_cell: TabCell,
            month: AccountingMonth,
            gigs_info: GigsInfo,
            vat_cell: TabCell
    ):
        super().__init__(top_left_cell, self.NUM_ROWS, month.num_weeks + 3, month, gigs_info)
        self.vat_cell = checked_type(vat_cell, TabRange)

    def format_requests(self):
        return [
            self.outline_border_request(),
            self[self.TITLE].merge_columns_request(),
            self[self.TITLE].center_text_request(),
            self[self.TITLE:self.WEEK + 1, :].set_bold_text_request(),
            self[-1, :].set_bold_text_request(),
            self[self.HIRE_FEES:self.BAR_TAKINGS + 1, 0].set_bold_text_request(),
            self[self.TOTAL, 0].set_bold_text_request(),
            self[self.WEEK].border_request(["bottom"]),
            self[self.WEEK:, 1].border_request(["left"]),
            self[self.WEEK:, -2].border_request(["left", "right"]),
            self.tab.group_rows_request(self.i_first_row + self.FULL,
                                        self.i_first_row + self.OTHER),
            self.tab.group_rows_request(self.i_first_row + self.Z_READING,
                                        self.i_first_row + self.CC_DOOR_TICKETS),
            self[self.WEEK, -2:].right_align_text_request(),
            self[self.FULL:self.OTHER + 1, 0].right_align_text_request(),
            self[self.CC_DOOR_TICKETS:self.CC_ARTIST_MERCH + 1, 0].right_align_text_request(),
            self[-1].offset(rows=1).border_request(["top"], style="SOLID_MEDIUM"),
            self[self.TICKET_SALES:, 1:].set_decimal_format_request("#,##0.00")
        ]

    def values(self):
        # Headings + Week nos + Total weekly ticket sales
        values = [(
            self[:, 0],
            ["Incoming", "", "Week", "Ticket Sales", "Full Price", "Members", "Student", "Other",
             "Hire Fees", "Bar Takings", "Total CC Takings", "CC Ticket Sales", "CC Artist Merch", "Total"]
        ), (
            self[self.WEEK, 1:-2],
            [w.week_no for w in self.weeks]
        ), (
            self[self.WEEK, -2:], ["MTD", "VAT Estimate"]
        ), (
            self[self.TICKET_SALES, 1:-2],
            [
                f"=SUM({self[self.FULL:self.OTHER + 1, i_col].in_a1_notation})"
                for i_col in range(1, self.num_weeks + 1)
            ]
        )]

        # Ticket values
        values += [
            (self[self.FULL + i, 1:-2], [w.ticket_sales(level) for w in self.gigs_by_week])
            for i, level in enumerate([TicketPriceLevel.FULL, TicketPriceLevel.MEMBER, TicketPriceLevel.CONCESSION])
        ]

        for i, func in enumerate([
            lambda w: w.other_ticket_sales,
            lambda w: w.hire_fees,
            lambda w: w.bar_takings
        ]):
            values.append(
                (self[self.OTHER + i, 1:-2], [func(w) for w in self.gigs_by_week])
            )

        # MTD values
        values += [
            (
                self[i_row, -2],
                f"=SUM({self[i_row, 1:self.num_weeks + 1].in_a1_notation})"
            )
            for i_row in range(self.TICKET_SALES, self.TOTAL + 1)
        ]

        # VAT
        for i_row in [self.TICKET_SALES, self.HIRE_FEES, self.BAR_TAKINGS]:
            mtd = self[i_row, -2].in_a1_notation
            vat = self.vat_cell.in_a1_notation
            values.append(
                (self[i_row, -1], f"=SUM({mtd} * {vat} / (1 + {vat}))")
            )

        # Bottom totals
        for i_week in range(self.num_weeks + 2):  # +2 for MTD + VAT
            ticket_sales_cell = self[self.TICKET_SALES, i_week + 1].in_a1_notation
            hire_fees_cell = self[self.HIRE_FEES, i_week + 1].in_a1_notation
            bar_takings_cell = self[self.BAR_TAKINGS, i_week + 1].in_a1_notation
            values.append(
                (self[self.TOTAL, i_week + 1], f"={ticket_sales_cell} + {hire_fees_cell} + {bar_takings_cell}")
            )

        return values


class OutgoingsRange(MonthAccountsRange):
    NUM_ROWS = 12

    TITLE, _, WEEK, MUSICIAN_COSTS, BAND_FEES, ACCOMMODATION, TRAVEL, CATERING, \
        SOUND_ENGINEERS, PRS, EVENING_PURCHASES, TOTAL = range(NUM_ROWS)

    def __init__(self, top_left_cell: TabCell, month: AccountingMonth, gigs_info: GigsInfo):
        super().__init__(
            top_left_cell,
            num_rows=self.NUM_ROWS,
            num_cols=month.num_weeks + 3,
            month=month,
            gigs_info=gigs_info)

    def format_requests(self):
        return [
            self.outline_border_request(),
            self[self.TITLE].merge_columns_request(),
            self[self.TITLE].center_text_request(),
            self[self.TITLE:self.MUSICIAN_COSTS + 1, :].set_bold_text_request(),
            self[self.TOTAL, :].set_bold_text_request(),
            self[self.SOUND_ENGINEERS:self.EVENING_PURCHASES + 1, 0].set_bold_text_request(),
            self[self.TOTAL, 0].set_bold_text_request(),
            self[self.WEEK].border_request(["bottom"]),
            self[self.WEEK:, 1].border_request(["left"]),
            self[self.WEEK:, -2].border_request(["left", "right"]),
            self.tab.group_rows_request(self.i_first_row + self.MUSICIAN_COSTS,
                                        self.i_first_row + self.CATERING),
            self[self.WEEK, -2:].right_align_text_request(),
            self[self.BAND_FEES:self.CATERING + 1, 0].right_align_text_request(),
            self[-1].offset(rows=1).border_request(["top"], style="SOLID_MEDIUM"),
            self[self.MUSICIAN_COSTS:, 1:].set_decimal_format_request("#,##0.00")
        ]

    def values(self):
        # Headings + Week nos + Total weekly ticket sales
        values = [(
            self[:, 0],
            ["Outgoing", "", "Week", "Musician Costs", "Fees", "Accomodation", "Travel", "Catering",
             "Sound Engineers", "PRS", "Evening Purchases", "Total"]
        ), (
            self[self.WEEK, 1:-2],
            [w.week_no for w in self.weeks]
        ), (
            self[self.WEEK, -2:], ["MTD", "VAT Estimate"]
        ), (
            self[self.MUSICIAN_COSTS, 1:-2],
            [
                f"=SUM({self[self.BAND_FEES:self.CATERING + 1, i_col].in_a1_notation})"
                for i_col in range(1, self.num_weeks + 1)
            ]
        )]

        for i_row, func in [
            (self.BAND_FEES, lambda w: w.musicians_fees),
            (self.ACCOMMODATION, lambda w: w.band_accommodation),
            (self.CATERING, lambda w: w.band_catering),
            (self.PRS, lambda w: w.prs_fee_ex_vat),
            (self.TRAVEL, lambda w: w.band_transport),
            (self.EVENING_PURCHASES, lambda w: w.evening_purchases),
        ]:
            values.append(
                (self[i_row, 1:-2], [func(w) for w in self.gigs_by_week])
            )

        # MTD values
        values += [
            (
                self[i_row, -2],
                f"=SUM({self[i_row, 1:self.num_weeks + 1].in_a1_notation})"
            )
            for i_row in range(self.MUSICIAN_COSTS, self.EVENING_PURCHASES + 1)
        ]

        # Bottom totals
        for i_week in range(self.num_weeks + 2):  # +2 for MTD + VAT
            cells = [
                self[row, i_week + 1].in_a1_notation
                for row in [self.MUSICIAN_COSTS, self.SOUND_ENGINEERS, self.PRS, self.EVENING_PURCHASES]
            ]
            text = " + ".join(cells)
            values.append(
                (self[self.TOTAL, i_week + 1], f"={text}")
            )

        return values


class MonthlyAccounts(Tab):
    def __init__(
            self,
            workbook: Workbook,
            month: AccountingMonth,
            vat_rate: Number,
            gigs_info: GigsInfo
    ):
        super().__init__(workbook, month.tab_name)
        self.month = checked_type(month, AccountingMonth)
        self.month_heading_range: MonthHeadingsRange = MonthHeadingsRange(self.cell("B2"), month, vat_rate)
        self.ticket_numbers_range = AudienceNumbersRange(
            self.cell("B6"),
            month.weeks,
            [w.week_no for w in month.weeks],
            gigs_info)
        self.income_range: IncomeRange = \
            IncomeRange(self.cell("B19"), month, gigs_info, self.month_heading_range.vat_cell)
        self.outgoings_range: OutgoingsRange = \
            OutgoingsRange(self.income_range.bottom_left_cell.offset(num_rows=2), month, gigs_info)
        if not self.workbook.has_tab(self.tab_name):
            self.workbook.add_tab(self.tab_name)

    def _workbook_format_requests(self):
        return self.delete_all_row_groups_requests() + [
            self.set_column_width_request(i_col=0, width=20),
            self.set_column_width_request(i_col=1, width=150),
        ]

    def update(self):
        format_requests = self.clear_values_and_formats_requests() \
                          + self._workbook_format_requests() \
                          + self.month_heading_range.format_requests() \
                          + self.ticket_numbers_range.format_requests() \
                          + self.income_range.format_requests() \
                          + self.outgoings_range.format_requests()

        self.workbook.batch_update(format_requests)
        self.workbook.batch_update_values(
            self.month_heading_range.values()
            + self.ticket_numbers_range.values()
            + self.income_range.values()
            + self.outgoings_range.values()
        )


if __name__ == '__main__':
    month = AccountingMonth(AccountingYear(2023), 12)
    contracts_and_events = VortexDB().contracts_and_events_for_period(month)
    accounts = MonthlyAccounts(Workbook(TEST_SHEET_ID), month, vat_rate=0.2, gigs_info=contracts_and_events)
    accounts.row_groups()
    accounts.update()
