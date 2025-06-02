from bank_statements.categorized_transaction import CategorizedTransactions
from bank_statements.payee_categories import PayeeCategory
from date_range.quarter import Quarter
from google_sheets import Tab, Workbook
from google_sheets.tab_range import TabRange, TabCell


class AnalysisRange(TabRange):

    HEADINGS = ["Quarter", "P&L Start", "P&L End", "Gigs", "Bar", "Building", "Salaries", "VAT", "Grants", "Operational", "Exceptional",
                "Balance"]
    (QUARTER, PNL_START, PNL_END, GIGS, BAR, BUILDING, SALARIES, VAT, GRANTS, OPERATIONAL, EXCEPTIONAL) = range(len(HEADINGS))


    def __init__(self, top_left_cell: TabCell, categorised_transactions: CategorizedTransactions):
        period = categorised_transactions.period
        q1 = Quarter.containing(period.first_day)
        q2 = Quarter.containing(period.last_day)
        self.quarters = [q1]
        while self.quarters[-1] < q2:
            self.quarters.append(self.quarters[-1] + 1)
        super().__init__(top_left_cell, num_rows=len(self.quarters) + 1,
                         num_cols=10)
        self.categorised_transactions = categorised_transactions

    def analysis_column(self, category: PayeeCategory):
        if category in [
            PayeeCategory.ACCOUNTANT
        ]:
            return None
        
    @property
    def values(self):
        rows = [self.HEADINGS]
        for q in self.quarters:
            trans = self.categorised_transactions.restrict_to_period(q)
        header = []

class AccountsAnalysisTab(Tab):

    def __init__(
            self,
            workbook: Workbook,
    ):
        super().__init__(workbook, tab_name="Analysis")
        if not self.workbook.has_tab(self.tab_name):
            self.workbook.add_tab(self.tab_name)

    def update(
        self,
        categorised_transactions: CategorizedTransactions,
    ):
        analysis_range = AnalysisRange(
            self.cell("B2"),
            categorised_transactions,

        )
