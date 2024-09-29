from decimal import Decimal
from typing import List

from bank_statements import BankActivity, Transaction
from bank_statements.bank_account import BankAccount
from bank_statements.categorized_transaction import CategorizedTransaction
from bank_statements.payee_categories import category_for_transaction, PayeeCategory
from date_range import Day, DateRange
from google_sheets import Tab, Workbook
from google_sheets.colors import LIGHT_GREEN, LIGHT_YELLOW
from google_sheets.tab_range import TabRange
from utils import checked_type


class StatementsTab(Tab):
    HEADINGS = ["Date", "Payee", "Amount", "Balance", "Category", "Type", "ID"]
    (DATE, PAYEE, AMOUNT, BALANCE, CATEGORY, TYPE, ID) = range(len(HEADINGS))

    def __init__(
            self,
            workbook: Workbook,
            account: BankAccount,
            title: str,
            period: DateRange
    ):
        super().__init__(workbook, tab_name=title)
        self.bank_account: BankAccount = checked_type(account, BankAccount)
        self.info_range = TabRange(self.cell("B2"), num_rows=5, num_cols=3)
        self.heading_range = TabRange(self.cell("B8"), num_rows=1, num_cols=len(self.HEADINGS))
        self.period: DateRange = period
        if not self.workbook.has_tab(self.tab_name):
            self.workbook.add_tab(self.tab_name)

    def update(self, bank_activity: BankActivity):
        sheet_transaction_infos = self.transaction_infos_from_tab()

        if bank_activity.non_empty:
            if bank_activity.first_date < self.period.first_day or bank_activity.last_date > self.period.last_day:
                raise ValueError(f"Bank activity is not within the period {self.period}")
        transactions = bank_activity.sorted_transactions
        full_range = TabRange(self.heading_range.top_left_cell, num_rows=1 + len(transactions),
                              num_cols=self.heading_range.num_cols)

        format_requests = self.clear_values_and_formats_requests() + [
            self.set_column_width_request(0, width=30)
        ]
        for col, width in [
            (self.DATE, 100),
            (self.PAYEE, 400),
            (self.AMOUNT, 100),
            (self.BALANCE, 100),
            (self.CATEGORY, 150),
            (self.TYPE, 100),
            (self.ID, 300),
        ]:
            format_requests.append(
                self.set_column_width_request(full_range.i_first_col + col, width=width)
            )

        format_requests.append(self.group_columns_request(
            self.heading_range.i_first_col + self.TYPE,
            self.heading_range.i_first_col + self.ID + 1,
        ))

        format_requests += [

            self.info_range[0, :].merge_columns_request(),
            self.info_range[0, :].center_text_request(),
            self.info_range[1:].right_align_text_request(),
            self.info_range[0:2, :].set_bold_text_request(),
            self.info_range[:, 0].set_bold_text_request(),
            self.info_range.outline_border_request(),
            self.info_range[3:, 1:].set_currency_format_request(),

            self.heading_range.set_bold_text_request(),
            self.heading_range.left_align_text_request(),
            self.heading_range[0, self.DATE].right_align_text_request(),
            self.heading_range[0, self.AMOUNT].right_align_text_request(),
            self.heading_range[0, self.BALANCE].right_align_text_request(),
            self.heading_range.background_colour_request(LIGHT_GREEN),

            full_range.outline_border_request(),
            full_range[:, :self.TYPE].border_request(["right"], style="SOLID_MEDIUM"),
            full_range[:, self.ID].left_align_text_request(),
            full_range[:, self.AMOUNT:self.BALANCE + 1].set_currency_format_request(),
        ]

        format_requests += [
            self.heading_range.offset(i, 0).background_colour_request(LIGHT_YELLOW)
            for i in range(1, len(transactions) + 1, 2)
        ]
        self.workbook.batch_update(format_requests)

        self.workbook.batch_update([self.collapse_all_groups_requests()])

        info_values = [
            [f"{self.bank_account.name} account transactions for {self.period}"],
            ["", "Start", "End"],
            ["Date", self.period.first_day, self.period.last_day],
            ["Balance", float(bank_activity.initial_balance), float(bank_activity.terminal_balance)],
            ["Uncategorized",
             "",
             f"=SUMIFS({full_range[:, self.AMOUNT].in_a1_notation}, {full_range[:, self.CATEGORY].in_a1_notation}, \"=\")"],
        ]

        transaction_values = [self.HEADINGS]

        def category_to_use(i_transaction, bank_transaction):
            if len(sheet_transaction_infos) == len(transactions):
                sheet_info = sheet_transaction_infos[i_transaction]
                sheet_category = sheet_info.category
                if sheet_category == "Bar Purchases":
                    return "Bar Stock"
                if sheet_info.transaction == bank_transaction:
                    if sheet_category is not None:
                        return sheet_category
            return category_for_transaction(bank_transaction)

        balance = bank_activity.initial_balance
        for i_trans, t in enumerate(transactions):
            balance += t.amount
            transaction_values.append(
                [
                    t.payment_date,
                    t.payee,
                    float(t.amount),
                    float(balance),
                    category_to_use(i_trans, t) or "",
                    t.transaction_type,
                    t.ftid,
                ]
            )

        transaction_range = TabRange(self.heading_range.top_left_cell, num_rows=1 + len(transactions),
                                     num_cols=len(self.HEADINGS))
        self.workbook.batch_update_values([
            (self.info_range, info_values),
            (transaction_range, transaction_values),
        ])

    def transaction_infos_from_tab(self) -> List[CategorizedTransaction]:
        def to_optional_value(cell_value):
            if isinstance(cell_value, str) and cell_value.strip() == "":
                return None
            return PayeeCategory(cell_value)

        def to_decimal(cell_value):
            if isinstance(cell_value, str):
                if cell_value.strip() == "":
                    return Decimal("0")
                return Decimal(cell_value.replace(",", ""))
            return Decimal(cell_value)

        infos = []
        values = self.read_values_for_columns(self.heading_range.columns_in_a1_notation)
        for row in values[self.heading_range.i_first_row + 1:]:
            payment_date = Day.parse(row[self.DATE])
            payee = row[self.PAYEE]
            amount = to_decimal(row[self.AMOUNT])
            transaction_type = row[self.TYPE]
            ftid = row[self.ID]
            category = to_optional_value(row[self.CATEGORY])
            transaction = Transaction(
                account=self.bank_account,
                ftid=ftid,
                payment_date=payment_date,
                payee=payee,
                amount=amount,
                transaction_type=transaction_type,
            )
            infos.append(CategorizedTransaction(transaction, category))
        return infos
