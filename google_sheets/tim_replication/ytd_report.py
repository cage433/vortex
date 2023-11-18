from date_range.accounting_month import AccountingMonth
from date_range.accounting_year import AccountingYear
from env import YTD_ACCOUNTS_SPREADSHEET_ID
from google_sheets import Tab, Workbook
from google_sheets.tab_range import TabRange, TabCell
from utils import checked_type


class HeadingsRange(TabRange):
    NUM_ROWS = 6
    NUM_COLS = 14

    def __init__(self, top_left_cell: TabCell, month: AccountingMonth):
        super().__init__(top_left_cell, num_rows=self.NUM_ROWS, num_cols=self.NUM_COLS)
        self.month = checked_type(month, AccountingMonth)

    def format_requests(self):
        return [
            self[0, 1:].merge_columns_request(),
            self[0, 1:].center_text_request(),
            self.set_bold_text_request()
        ]

    def values(self) -> list[type[TabRange, list[list[any]]]]:
        month_name = self.month.month_name
        return [
            (self[0, 1], f"Gig Report Month 12 - {month_name}"),
            (self[1, 0], ["Vortex Jazz Club"]),
            (self[2, 0:2], ["Income and Expenditure", f"Year end {month_name}"]),
            (self[3, 0:2], ["Month", month_name]),
            (self[5, 1:],
             [
                 (self.month.year.first_month + i).month_name
                 for i in range(12)
             ] + ["Total"]
             ),
        ]


class YTD_Report(Tab):
    def __init__(
            self,
            workbook: Workbook,
            month: AccountingMonth,
    ):
        super().__init__(workbook, tab_name=month.month_name)
        self.month: AccountingMonth = checked_type(month, AccountingMonth)
        self.headings_range = HeadingsRange(self.cell("B1"), self.month)
        if not self.workbook.has_tab(self.tab_name):
            self.workbook.add_tab(self.tab_name)

    def _workbook_format_requests(self):
        return self.delete_all_row_groups_requests() + [
            self.set_column_width_request(i_col=1, width=200),
            self.set_columns_width_request(i_first_col=2, i_last_col=14, width=100),
        ]

    def update(self):
        format_requests = self.clear_values_and_formats_requests() \
                          + self._workbook_format_requests() \
                          + self.headings_range.format_requests()
        self.workbook.batch_update(format_requests)
        self.workbook.batch_update_values(
            self.headings_range.values(),
            value_input_option="RAW"            # Prevent creation of dates
        )


if __name__ == '__main__':
    workbook = Workbook(YTD_ACCOUNTS_SPREADSHEET_ID)
    tab = YTD_Report(workbook, AccountingMonth(AccountingYear(2023), 8))
    tab.update()
