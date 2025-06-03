import shelve
from decimal import Decimal
from pathlib import Path
from typing import List, Any

from bank_statements import BankActivity, Transaction
from bank_statements.Transactions import Transactions
from bank_statements.bank_account import CURRENT_ACCOUNT, SAVINGS_ACCOUNT, CHARITABLE_ACCOUNT, BBL_ACCOUNT, BankAccount
from bank_statements.categorize import category_for_transaction
from bank_statements.payee_categories import PayeeCategory
from date_range import Day, DateRange
from date_range.accounting_month import AccountingMonth
from env import BANK_TRANSACTIONS_2025_ID, BANK_TRANSACTIONS_2024_ID, \
    BANK_TRANSACTIONS_2023_ID, BANK_TRANSACTIONS_2022_ID, BANK_TRANSACTIONS_2021_ID, \
    BANK_TRANSACTIONS_2020_ID
from google_sheets import Tab, Workbook
from google_sheets.colors import LIGHT_GREEN, LIGHT_YELLOW
from google_sheets.tab_range import TabRange

SHELF = Path(__file__).parent / "_categorised_transactions.shelf"

class StatementsTab(Tab):
    accounts = [CURRENT_ACCOUNT, SAVINGS_ACCOUNT, CHARITABLE_ACCOUNT, BBL_ACCOUNT]
    HEADINGS = ["Date", "Account", "Payee", "", "Category", "Amount", "Current", "Savings", "Charitable", "BBL",
                "Balance"]
    (DATE, ACCOUNT, PAYEE, BLANK, CATEGORY, AMOUNT, CURRENT, SAVINGS, CHARITABLE, BBL, BALANCE) = range(len(HEADINGS))

    (INFO_ROW_1, INFO_ROW_2, INFO_DATE, INFO_BALANCE, INFO_CURRENT, INFO_SAVINGS, INFO_CHARITABLE, INFO_BBL,
     INFO_UNCATEGORISED) = range(9)

    def __init__(
            self,
            workbook: Workbook,
            title: str,
            period: DateRange
    ):
        super().__init__(workbook, tab_name=title)
        self.info_range = TabRange(self.cell("B2"), num_rows=10, num_cols=3)
        self.heading_range = TabRange(self.info_range.bottom_left_cell.offset(2, 0), num_rows=1,
                                      num_cols=len(self.HEADINGS))
        self.period: DateRange = period
        if not self.workbook.has_tab(self.tab_name):
            self.workbook.add_tab(self.tab_name)

    def clear_all(self):
        format_requests = self.clear_values_and_formats_requests()
        self.workbook.batch_update(format_requests)

    def update(self, bank_activity: BankActivity):

        tab_categorised_transactions = self.transactions_from_tab()

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
            (self.ACCOUNT, 100),
            (self.PAYEE, 100),
            (self.BLANK, 200),
            (self.CATEGORY, 120),
            (self.AMOUNT, 100),
            (self.CURRENT, 100),
            (self.SAVINGS, 100),
            (self.CHARITABLE, 100),
            (self.BBL, 100),
            (self.BALANCE, 100),
        ]:
            format_requests.append(
                self.set_column_width_request(full_range.i_first_col + col, width=width)
            )

        format_requests.append(self.group_rows_request(
            self.info_range.i_first_row + self.INFO_CURRENT,
            self.info_range.i_first_row + self.INFO_BBL
        ))
        format_requests.append(self.group_columns_request(
            full_range.i_first_col + self.CURRENT,
            full_range.i_first_col + self.BBL
        ))
        format_requests.append(self.freeze_rows_request(self.heading_range.i_first_row + 1))
        format_requests += [

            self.info_range[0, :].merge_columns_request(),
            self.info_range[0, :].center_text_request(),
            self.info_range[self.INFO_ROW_2:].right_align_text_request(),
            self.info_range[self.INFO_ROW_1:self.INFO_ROW_2 + 1, :].set_bold_text_request(),
            self.info_range[:, 0].set_bold_text_request(),
            self.info_range.outline_border_request(),
            self.info_range[self.INFO_CURRENT, :].border_request(["top"]),
            self.info_range[self.INFO_BBL, :].border_request(["bottom"]),
            self.info_range[self.INFO_BALANCE:, 1:].set_currency_format_request(),

            self.heading_range[0, self.PAYEE:self.PAYEE + 2].merge_columns_request(),
            self.heading_range.set_bold_text_request(),
            self.heading_range.left_align_text_request(),
            self.heading_range[0, self.DATE].right_align_text_request(),
            self.heading_range[0, self.AMOUNT:self.BALANCE + 1].right_align_text_request(),
            self.heading_range.background_colour_request(LIGHT_GREEN),

            full_range.outline_border_request(),
            full_range[:, self.CURRENT].border_request(["left"]),
            full_range[:, self.BBL].border_request(["right"]),
            full_range[:, self.BALANCE].left_align_text_request(),
            full_range[:, self.AMOUNT:self.BALANCE + 1].set_currency_format_request(),
        ]
        for i_row in range(full_range.num_rows):
            format_requests.append(
                full_range[i_row, self.PAYEE:self.PAYEE + 2].merge_columns_request(),
            )

        format_requests += [
            self.heading_range.offset(i, 0).background_colour_request(LIGHT_YELLOW)
            for i in range(1, len(transactions) + 1, 2)
        ]
        self.workbook.batch_update(format_requests)

        self.workbook.batch_update([self.collapse_all_groups_requests()])

        info_values = [
            [f"Transactions for {self.period}"],
            ["", "Start", "End"],
            ["Date", self.period.first_day, self.period.last_day]
        ]
        net_formulae = [
            "Balance",
            f"=SUM({self.info_range[4:8, 1].in_a1_notation})",
            f"=SUM({self.info_range[4:8, 2].in_a1_notation})",
        ]
        info_values.append(net_formulae)

        for account in self.accounts:
            info_values.append(
                [account.name, float(bank_activity.initial_balance(account) or Decimal("0")),
                 float(bank_activity.terminal_balance(account) or Decimal("0"))]
            )
        info_values.append(["", "", ""])
        info_values.append(
            ["Uncategorized",
             "",
             f"=SUMIFS({full_range[:, self.AMOUNT].in_a1_notation}, {full_range[:, self.CATEGORY].in_a1_notation}, \"=\")"]
        )

        transaction_values: List[List[Any]] = [self.HEADINGS]

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

        balances = {acc: bank_activity.initial_balance(acc) for acc in self.accounts}
        for i_trans, t in enumerate(transactions):
            balances[t.account] += t.amount
            is_first_or_last_row = i_trans == len(transactions) - 1 or i_trans == 0
            balances_row = [
                float(balances[acc] or Decimal("0")) if acc == t.account or is_first_or_last_row else ""
                for acc in self.accounts
            ]
            net_balance = sum(balances[acc] or Decimal("0") for acc in self.accounts)

            transaction_values.append(
                [
                    t.payment_date,
                    t.account.name,
                    t.payee,
                    "",
                    category_cell_value(i_trans, t),
                    float(t.amount),
                ] + balances_row +
                [float(net_balance)]
            )

        transaction_range = TabRange(self.heading_range.top_left_cell, num_rows=1 + len(transactions),
                                     num_cols=len(self.HEADINGS))
        self.workbook.batch_update_values([
            (self.info_range, info_values),
            (transaction_range, transaction_values),
        ])

    def transactions_from_tab(self) -> Transactions:

        def to_payee_category(cell_value: str) -> PayeeCategory:
            if isinstance(cell_value, str) and cell_value.strip() == "":
                return PayeeCategory.UNCATEGORISED
            return PayeeCategory(cell_value)

        def to_decimal(cell_value):
            if isinstance(cell_value, str):
                if cell_value.strip() == "":
                    return Decimal("0")
                return Decimal(cell_value.replace(",", ""))
            return Decimal(cell_value)

        trans = []
        values = self.read_values_for_columns(self.heading_range.columns_in_a1_notation)
        for row in values[self.heading_range.i_first_row + 1:]:
            payment_date = Day.parse(row[self.DATE])
            payee = row[self.PAYEE]
            amount = to_decimal(row[self.AMOUNT])
            account = BankAccount.from_name(row[self.ACCOUNT])
            category = to_payee_category(row[self.CATEGORY])
            transaction = Transaction(
                account=account,
                category=category,
                payment_date=payment_date,
                payee=payee,
                amount=amount,
            )
            trans.append(transaction)
        return Transactions(trans)

    @staticmethod
    def sheet_id_for_month(month: AccountingMonth) -> str:
        year = month.year.y
        if year == 2020:
            return BANK_TRANSACTIONS_2020_ID
        if year == 2021:
            return BANK_TRANSACTIONS_2021_ID
        if year == 2022:
            return BANK_TRANSACTIONS_2022_ID
        if year == 2023:
            return BANK_TRANSACTIONS_2023_ID
        elif year == 2024:
            return BANK_TRANSACTIONS_2024_ID
        if year == 2025:
            return BANK_TRANSACTIONS_2025_ID
        raise ValueError(f"Unsupported month {month} for all statements tab")

    @staticmethod
    def transactions_for_month(acc_month: AccountingMonth, force: bool) -> Transactions:
        key = f"current_account_transactions Acc Month {acc_month}"
        with shelve.open(str(SHELF)) as shelf:
            if key not in shelf or force:
                print(f"Processing {acc_month}")
                transactions = StatementsTab(
                    Workbook(StatementsTab.sheet_id_for_month(acc_month)),
                    acc_month.month_name,
                    acc_month
                ).transactions_from_tab()
                shelf[key] = transactions
            return shelf[key]


    @staticmethod
    def transactions(period: DateRange, force: bool) -> Transactions:
        key = f"current_account_transactions Period {period}"
        with shelve.open(str(SHELF)) as shelf:
            has_value = key in shelf
            if has_value and not force:
                return shelf[key]
        acc_month = AccountingMonth.containing(period.first_day)
        last_acc_month = AccountingMonth.containing(period.last_day)
        transactions = Transactions([])
        while acc_month <= last_acc_month:
            transactions += StatementsTab.transactions_for_month(acc_month, force)
            acc_month += 1
        with shelve.open(str(SHELF)) as shelf:
            shelf[key] = transactions.restrict_to_period(period)
            return shelf[key]
