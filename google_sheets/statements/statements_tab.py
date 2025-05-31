from decimal import Decimal
from typing import List, Optional

from bank_statements import BankActivity, Transaction
from bank_statements.bank_account import BankAccount, CURRENT_ACCOUNT
from bank_statements.categorized_transaction import CategorizedTransaction
from bank_statements.payee_categories import category_for_transaction, PayeeCategory
from date_range import Day, DateRange
from date_range.accounting_month import AccountingMonth
from env import CURRENT_ACCOUNT_2023_STATEMENTS_ID, CURRENT_ACCOUNT_2024_STATEMENTS_ID, \
    CURRENT_ACCOUNT_2025_STATEMENTS_ID, CURRENT_ACCOUNT_2022_STATEMENTS_ID, CURRENT_ACCOUNT_2021_STATEMENTS_ID, \
    CURRENT_ACCOUNT_2020_STATEMENTS_ID
from google_sheets import Tab, Workbook
from google_sheets.colors import LIGHT_GREEN, LIGHT_YELLOW
from google_sheets.tab_range import TabRange
from utils import checked_type


class StatementsTab(Tab):
    HEADINGS = ["Date", "Payee", "Amount", "Balance", "Category", "Type"]
    (DATE, PAYEE, AMOUNT, BALANCE, CATEGORY, TYPE) = range(len(HEADINGS))

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
        tab_categorised_transactions = self.categorised_transactions_from_tab()

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
        ]:
            format_requests.append(
                self.set_column_width_request(full_range.i_first_col + col, width=width)
            )

        format_requests.append(self.group_columns_request(
            self.heading_range.i_first_col + self.TYPE,
            self.heading_range.i_first_col + self.TYPE + 1,
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
            full_range[:, self.TYPE].left_align_text_request(),
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

        def category_cell_value(i_transaction, bank_transaction):
            cell_category = ""
            if len(tab_categorised_transactions) == len(transactions):
                categorised_transaction = tab_categorised_transactions[i_transaction]
                sheet_category = categorised_transaction.category
                if categorised_transaction.transaction == bank_transaction:
                    cell_category = sheet_category
            if cell_category == "" or cell_category == PayeeCategory.UNCATEGORISED:
                cell_category = category_for_transaction(bank_transaction)
            if cell_category == PayeeCategory.UNCATEGORISED:
                return ""
            return cell_category

        balance = bank_activity.initial_balance
        for i_trans, t in enumerate(transactions):
            balance += t.amount
            transaction_values.append(
                [
                    t.payment_date,
                    t.payee,
                    float(t.amount),
                    float(balance),
                    category_cell_value(i_trans, t),
                    t.transaction_type,
                ]
            )

        transaction_range = TabRange(self.heading_range.top_left_cell, num_rows=1 + len(transactions),
                                     num_cols=len(self.HEADINGS))
        self.workbook.batch_update_values([
            (self.info_range, info_values),
            (transaction_range, transaction_values),
        ])

    def categorised_transactions_from_tab(self) -> List[CategorizedTransaction]:
        # The Kashflow categories differ slightly from Tim's payee categories.
        # For now we'll map them, but eventually we can probably just use the Kashflow categories.
        # We also use this to repair categories, as they get redefined
        def to_payee_category(payee:str, cell_value:str) -> PayeeCategory:
            if isinstance(cell_value, str) and cell_value.strip() == "":
                return PayeeCategory.UNCATEGORISED
            if cell_value == "Administration":
                return PayeeCategory.ACCOUNTANT
            if cell_value == "Bar Purchases":
                return PayeeCategory.BAR_STOCK
            if cell_value == "Toilet Tissues":
                return PayeeCategory.OPERATIONAL_COSTS
            if cell_value == "Tickets":
                return PayeeCategory.MEMBERSHIPS
            if cell_value.startswith("Marketing"):
                return PayeeCategory.MARKETING
            if cell_value.startswith("Licensing"):
                return PayeeCategory.LICENSING
            if payee.startswith("Denise Williams"):
                return PayeeCategory.GIG_SECURITY
            if cell_value == "Security":
                return PayeeCategory.BUILDING_SECURITY
            if cell_value == "Copyright Infringement":
                return PayeeCategory.OPERATIONAL_COSTS
            if cell_value == "Rehearsal":
                return PayeeCategory.SPACE_HIRE
            if cell_value == "Equipment Rental":
                return PayeeCategory.EQUIPMENT_HIRE
            if cell_value == "Staff Costs":
                return PayeeCategory.SALARIES
            if cell_value == "Musicians Costs":
                return PayeeCategory.MUSICIAN_COSTS
            if cell_value == "Petty cash":
                return PayeeCategory.PETTY_CASH
            if cell_value == "Ticket sales":
                return PayeeCategory.TICKET_SALES
            if cell_value == "Zettle Credits":
                return PayeeCategory.CARD_SALES
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
            category = to_payee_category(payee, row[self.CATEGORY])
            transaction = Transaction(
                account=self.bank_account,
                payment_date=payment_date,
                payee=payee,
                amount=amount,
                transaction_type=transaction_type,
            )
            infos.append(CategorizedTransaction(transaction, category))
        return infos

    @staticmethod
    def sheet_id_for_account(account: BankAccount, month: AccountingMonth) -> str:
        if account == CURRENT_ACCOUNT:
            year = month.year.y
            if year == 2020:
                return CURRENT_ACCOUNT_2020_STATEMENTS_ID
            if year == 2021:
                return CURRENT_ACCOUNT_2021_STATEMENTS_ID
            if year == 2022:
                return CURRENT_ACCOUNT_2022_STATEMENTS_ID
            if year == 2023:
                return CURRENT_ACCOUNT_2023_STATEMENTS_ID
            elif year == 2024:
                return CURRENT_ACCOUNT_2024_STATEMENTS_ID
            elif year == 2025:
                return CURRENT_ACCOUNT_2025_STATEMENTS_ID
        raise ValueError(f"Unrecognized account/month {account}/{month}")

