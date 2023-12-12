from airtable_db.contracts_and_events import GigsInfo
from google_sheets import Workbook, Tab
from google_sheets.ticket_sales.vortex_summary_range import AudienceRange, TicketSalesRange, BarTakingsRange, \
    BarProfitRange, RehearsalAndHireFeesRange
from kashflow.nominal_ledger import NominalLedger


class VortexSummaryTab(Tab):

    def __init__(
            self,
            workbook: Workbook,
            title: str,
            gigs_info: GigsInfo,
            nominal_ledger: NominalLedger,
    ):
        super().__init__(workbook, tab_name=title)
        self.audience_range = AudienceRange(
            self.cell("B2"),
            gigs_info,
        )
        self.ticket_sales_range = TicketSalesRange(
            self.audience_range.bottom_left_cell.offset(num_rows=2),
            gigs_info,
        )
        self.bar_takings_range = BarTakingsRange(
            self.ticket_sales_range.bottom_left_cell.offset(num_rows=2),
            gigs_info,
        )
        self.bar_profit_range = BarProfitRange(
            self.bar_takings_range.bottom_left_cell.offset(num_rows=2),
            gigs_info,
            nominal_ledger,
        )
        self.hire_fees_range = RehearsalAndHireFeesRange(
            self.bar_profit_range.bottom_left_cell.offset(num_rows=2),
            gigs_info,
            nominal_ledger,
        )
        if not self.workbook.has_tab(self.tab_name):
            self.workbook.add_tab(self.tab_name)

    def update(self):
        self.workbook.batch_update(
            self.clear_values_and_formats_requests() +
            self.audience_range.format_requests() +
            self.ticket_sales_range.format_requests() +
            self.bar_takings_range.format_requests() +
            self.bar_profit_range.format_requests() +
            self.hire_fees_range.format_requests() +
            []
        )

        self.workbook.batch_update_values(
            self.audience_range.values() +
            self.ticket_sales_range.values() +
            self.bar_takings_range.values() +
            self.bar_profit_range.values() +
            self.hire_fees_range.values() +
            []
        )

