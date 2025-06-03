from accounting.accounting_activity import AccountingActivity
from airtable_db.gigs_info import GigsInfo
from bank_statements.Transactions import Transactions
from date_range import DateRange, Day
from date_range.simple_date_range import SimpleDateRange
from env import GIG_ANALYSIS_ID
from google_sheets import Tab, Workbook
from google_sheets.gigs.gig_analysis_ranges import GigNumbersRange, AirtableTicketSalesRange, BankTicketSalesRange, \
    BankDrinkSalesRange, BankDrinkSalesPerCustomerRange, AirtableDrinkSalesRange, AirtableDrinkSalesPerCustomerRange, \
    AirtableNumTicketsSoldRange
from google_sheets.statements.statements_tab import StatementsTab


class GigAnalysisTab(Tab):
    def __init__(
            self,
            workbook: Workbook,
            period: DateRange,
            short_period: DateRange,
            gigs_info: GigsInfo,
            transactions: Transactions
    ):
        super().__init__(workbook, tab_name="Gig Analysis")
        self.gig_numbers_range = GigNumbersRange(
            self.cell("B2"),
            period,
            gigs_info
        )
        self.num_tickets_sold = AirtableNumTicketsSoldRange(
            self.gig_numbers_range.bottom_left_cell.offset(num_rows=2),
            period,
            gigs_info
        )
        self.airtable_ticket_sales_range = AirtableTicketSalesRange(
            self.num_tickets_sold.bottom_left_cell.offset(num_rows=2),
            period,
            gigs_info
        )
        self.airtable_drink_sales = AirtableDrinkSalesRange(
            self.airtable_ticket_sales_range.bottom_left_cell.offset(num_rows=2),
            period,
            gigs_info,
        )
        self.airtable_drink_sales_per_customer = AirtableDrinkSalesPerCustomerRange(
            self.airtable_drink_sales.bottom_left_cell.offset(num_rows=2),
            period,
            gigs_info,
        )

        self.bank_ticket_sales = BankTicketSalesRange(
            self.airtable_drink_sales_per_customer.bottom_left_cell.offset(num_rows=5),
            short_period,
            transactions,
            gigs_info,
        )
        self.bank_drink_sales = BankDrinkSalesRange(
            self.bank_ticket_sales.bottom_left_cell.offset(num_rows=2),
            short_period,
            transactions,
            gigs_info,
        )
        self.bank_drink_sales_per_customer = BankDrinkSalesPerCustomerRange(
            self.bank_drink_sales.bottom_left_cell.offset(num_rows=2),
            short_period,
            transactions,
            gigs_info,
        )
        self.ranges = [
            self.gig_numbers_range,
            self.num_tickets_sold,
            self.airtable_ticket_sales_range,
            self.airtable_drink_sales,
            self.airtable_drink_sales_per_customer,
            self.bank_ticket_sales,
            self.bank_drink_sales,
            self.bank_drink_sales_per_customer
        ]
        if not self.workbook.has_tab(self.tab_name):
            self.workbook.add_tab(self.tab_name)

    def _workbook_format_requests(self):
        reqs = []
        for range in self.ranges:
            reqs += range.format_requests()
        return reqs


    def update(self):
        self.workbook.batch_update(
            self.clear_values_and_formats_requests() +
            self._workbook_format_requests()
        )

        values = []
        for range in self.ranges:
            values += range.values()
        self.workbook.batch_update_values(values)


if __name__ == '__main__':
    force = False
    workbook = Workbook(GIG_ANALYSIS_ID)

    period = SimpleDateRange(
        Day(2018, 1, 1),
        Day.today()
    )
    gig_info = AccountingActivity.gig_info_for_period(period, force=force)
    trans_period = SimpleDateRange(
        Day(2019, 9, 2),
        Day.today()
    )
    categorised_transactions = StatementsTab.transactions(trans_period, force=force)
    tab = GigAnalysisTab(workbook, period, trans_period, gig_info, categorised_transactions)

    tab.update()
