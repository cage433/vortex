from decimal import Decimal
from typing import List

from bank_statements import BankActivity, Transaction
from bank_statements.bank_account import BankAccount
from date_range import Day, DateRange
from google_sheets import Tab, Workbook
from google_sheets.colors import LIGHT_GREEN, LIGHT_YELLOW
from google_sheets.tab_range import TabRange
from myopt.nothing import Nothing
from myopt.opt import Opt
from utils import checked_type


class TransactionInfo:
    def __init__(
            self,
            transaction: Transaction,
            balance: Decimal,
            confirmed: bool
    ):
        self.transaction: Transaction = checked_type(transaction, Transaction)
        self.balance: Decimal = checked_type(balance, Decimal)
        self.confirmed: bool = checked_type(confirmed, bool)


class StatementsTab(Tab):
    HEADINGS = ["Date", "Payee", "Amount", "Balance", "Category", "Confirmed", "Type", "ID"]
    (DATE, PAYEE, AMOUNT, BALANCE, CATEGORY, CONFIRMED, TYPE, ID) = range(len(HEADINGS))

    def __init__(
            self,
            workbook: Workbook,
            account: BankAccount,
            title: str,
            period: DateRange
    ):
        super().__init__(workbook, tab_name=title)
        self.bank_account: BankAccount = checked_type(account, BankAccount)
        self.info_range = TabRange(self.cell("B2"), num_rows=4, num_cols=3)
        self.heading_range = TabRange(self.cell("B7"), num_rows=1, num_cols=len(self.HEADINGS))
        self.period: DateRange = period
        if not self.workbook.has_tab(self.tab_name):
            self.workbook.add_tab(self.tab_name)

    def update(self, bank_activity: BankActivity):
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
            (self.PAYEE, 250),
            (self.AMOUNT, 100),
            (self.BALANCE, 100),
            (self.CATEGORY, 150),
            (self.CONFIRMED, 100),
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
            self.info_range[3, 1:].set_decimal_format_request("#,##0.00"),

            self.heading_range.set_bold_text_request(),
            self.heading_range.left_align_text_request(),
            self.heading_range[0, self.DATE].right_align_text_request(),
            self.heading_range[0, self.AMOUNT].right_align_text_request(),
            self.heading_range[0, self.BALANCE].right_align_text_request(),
            self.heading_range.background_colour_request(LIGHT_GREEN),

            full_range.outline_border_request(),
            full_range[:, :self.TYPE].border_request(["right"], style="SOLID_MEDIUM"),
            full_range[:, self.ID].left_align_text_request(),
            full_range[:, self.AMOUNT:self.BALANCE + 1].set_decimal_format_request("#,##0.00"),
            self.collapse_all_groups_requests()
        ]

        format_requests += [
            self.heading_range.offset(i, 0).background_colour_request(LIGHT_YELLOW)
            for i in range(1, len(transactions) + 1, 2)
        ]
        self.workbook.batch_update(format_requests)

        info_values = [
            [f"{self.bank_account.name} account transactions for {self.period}"],
            ["", "Start", "End"],
            ["Date", self.period.first_day, self.period.last_day],
            ["Balance", float(bank_activity.initial_balance), float(bank_activity.terminal_balance)]
        ]

        transaction_values = [
            self.HEADINGS
        ]
        balance = bank_activity.initial_balance
        for t in transactions:
            balance += t.amount
            transaction_values.append(
                [
                    t.payment_date,
                    t.payee,
                    float(t.amount),
                    float(balance),
                    t.category.get_or_else(""),
                    False,
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

    def transaction_infos_from_tab(self) -> List[TransactionInfo]:
        def to_opt(cell_value):
            if cell_value == "":
                return Nothing()
            return Opt.of(cell_value)

        def to_decimal(cell_value):
            if cell_value == "":
                return Decimal("0")
            if isinstance(cell_value, str):
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
            category = to_opt(row[self.CATEGORY])
            balance = to_decimal(row[self.BALANCE])
            confirmed = to_opt(row[self.CONFIRMED]).map(bool).get_or_else(False)
            transaction = Transaction(
                account=self.bank_account.id,
                ftid=ftid,
                payment_date=payment_date,
                payee=payee,
                amount=amount,
                transaction_type=transaction_type,
                category=category,
            )
            infos.append(TransactionInfo(transaction, balance, confirmed))
        return infos
