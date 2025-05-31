from decimal import Decimal
from typing import List, Any, Optional

from bank_statements import BankActivity, Transaction
from bank_statements.bank_account import CURRENT_ACCOUNT, SAVINGS_ACCOUNT, CHARITABLE_ACCOUNT, BBL_ACCOUNT, BankAccount
from bank_statements.categorized_transaction import CategorizedTransaction
from bank_statements.payee_categories import category_for_transaction, PayeeCategory
from date_range import Day, DateRange
from date_range.accounting_month import AccountingMonth
from env import ALL_ACCOUNTS_2025_STATEMENTS_ID
from google_sheets import Tab, Workbook
from google_sheets.colors import LIGHT_GREEN, LIGHT_YELLOW
from google_sheets.tab_range import TabRange


class AllStatementsTab(Tab):
    accounts = [CURRENT_ACCOUNT, SAVINGS_ACCOUNT, CHARITABLE_ACCOUNT, BBL_ACCOUNT]
    HEADINGS = ["Date", "Account", "Payee", "Category", "Amount", "Current", "Savings", "Charitable", "BBL", "Balance"]
    (DATE, ACCOUNT, PAYEE, CATEGORY, AMOUNT, CURRENT, SAVINGS, CHARITABLE, BBL, BALANCE) = range(len(HEADINGS))

    def __init__(
            self,
            workbook: Workbook,
            title: str,
            period: DateRange
    ):
        super().__init__(workbook, tab_name=title)
        self.info_range = TabRange(self.cell("B2"), num_rows=9, num_cols=3)
        self.heading_range = TabRange(self.info_range.bottom_left_cell.offset(2, 0), num_rows=1,
                                      num_cols=len(self.HEADINGS))
        self.period: DateRange = period
        if not self.workbook.has_tab(self.tab_name):
            self.workbook.add_tab(self.tab_name)

    def update(self, bank_activity: BankActivity, old_current_account_infos: List[CategorizedTransaction]):
        categories_by_date_and_payee = {
            (t.payment_date, t.payee): t.category
            for t in old_current_account_infos
        }

        def update_transaction_category(transaction: CategorizedTransaction) -> CategorizedTransaction:
            if transaction.account == CURRENT_ACCOUNT:
                key = (transaction.payment_date, transaction.payee)
                if key in categories_by_date_and_payee:
                    return transaction.with_category(categories_by_date_and_payee[key])
                print("here")
            return transaction

        tab_categorised_transactions = [
            update_transaction_category(t) for t in self.categorised_transactions_from_tab()
        ]

        for t in tab_categorised_transactions:
            if t.category == PayeeCategory.UNCATEGORISED or t.category is None:
                print("here")
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
            (self.PAYEE, 200),
            (self.CATEGORY, 100),
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
            self.info_range.i_first_row + 4,
            self.info_range.i_first_row + 7
            ))
        format_requests += [

            self.info_range[0, :].merge_columns_request(),
            self.info_range[0, :].center_text_request(),
            self.info_range[1:].right_align_text_request(),
            self.info_range[0:2, :].set_bold_text_request(),
            self.info_range[:, 0].set_bold_text_request(),
            self.info_range.outline_border_request(),
            self.info_range[4, :].border_request(["top"]),
            self.info_range[7, :].border_request(["bottom"]),
            self.info_range[3:, 1:].set_currency_format_request(),

            self.heading_range.set_bold_text_request(),
            self.heading_range.left_align_text_request(),
            self.heading_range[0, self.DATE].right_align_text_request(),
            self.heading_range[0, self.AMOUNT:self.BALANCE + 1].right_align_text_request(),
            self.heading_range.background_colour_request(LIGHT_GREEN),

            full_range.outline_border_request(),
            full_range[:, :self.BALANCE].border_request(["right"], style="SOLID_MEDIUM"),
            full_range[:, self.BALANCE].left_align_text_request(),
            full_range[:, self.AMOUNT:self.BALANCE + 1].set_currency_format_request(),
        ]

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
                [account.name, float(bank_activity.initial_balance(account)),
                 float(bank_activity.terminal_balance(account))]
            )
        info_values.append(
            ["Uncategorized",
             "",
             f"=SUMIFS({full_range[:, self.AMOUNT].in_a1_notation}, {full_range[:, self.CATEGORY].in_a1_notation}, \"=\")"]
        )

        transaction_values: List[List[Any]] = [self.HEADINGS]

        def category_cell_value(i_transaction, bank_transaction):
            key = (bank_transaction.payment_date, bank_transaction.payee)
            if key in categories_by_date_and_payee:
                category = categories_by_date_and_payee[key]
                if category != PayeeCategory.UNCATEGORISED:
                    return category
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
                float(balances[acc]) if acc == t.account or is_first_or_last_row else ""
                for acc in self.accounts
            ]
            net_balance = sum(balances[acc] for acc in self.accounts)

            foo = category_cell_value(i_trans, t)
            if foo == "":
                print("here")
            transaction_values.append(
                [
                    t.payment_date,
                    t.account.name,
                    t.payee,
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

    def categorised_transactions_from_tab(self) -> List[CategorizedTransaction]:

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

        infos = []
        values = self.read_values_for_columns(self.heading_range.columns_in_a1_notation)
        for row in values[self.heading_range.i_first_row + 1:]:
            payment_date = Day.parse(row[self.DATE])
            payee = row[self.PAYEE]
            amount = to_decimal(row[self.AMOUNT])
            i_acc = next(i for i in range(4) if float(to_decimal(row[self.CURRENT + i])) != 0)
            account = self.accounts[i_acc]
            category = to_payee_category(row[self.CATEGORY])
            transaction = Transaction(
                account=account,
                payment_date=payment_date,
                payee=payee,
                amount=amount,
            )
            infos.append(CategorizedTransaction(transaction, category))
        return infos

    @staticmethod
    def sheet_id_for_month(month: AccountingMonth) -> str:
        year = month.year.y
        if year == 2025:
            return ALL_ACCOUNTS_2025_STATEMENTS_ID
        raise ValueError(f"Unsupported month {month} for all statements tab")
