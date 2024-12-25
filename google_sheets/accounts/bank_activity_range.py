from typing import List

from accounting.accounting_activity import AccountingActivity
from bank_statements.bank_account import CURRENT_ACCOUNT
from bank_statements.categorized_transaction import CategorizedTransactions, CategorizedTransaction
from bank_statements.payee_categories import PayeeCategory
from date_range import DateRange
from google_sheets.tab_range import TabRange, TabCell
from utils import checked_type, checked_list_type


class BankActivityRange(TabRange):
    NUM_COLUMNS = 10
    CATEGORY_COLUMN, _, _, PERIOD_COLUMN, DATE_COLUMN, ACCOUNT_COLUMN, PAYEE_COLUMN, _, _, AMOUNT_COLUMN = range(NUM_COLUMNS)

    def __init__(self, top_left_cell: TabCell, accounting_activity: AccountingActivity, periods: List[DateRange]):
        other_bank_accounts = [a for a in accounting_activity.bank_activity.accounts if a != CURRENT_ACCOUNT]
        self.categorised_transactions: CategorizedTransactions = CategorizedTransactions(
            [
                CategorizedTransaction(t, category=PayeeCategory.UNCATEGORISED)
                for t in
                accounting_activity.bank_activity.restrict_to_accounts(*other_bank_accounts).sorted_transactions
            ]

        ) + accounting_activity.current_account_transactions
        self.num_rows = BankActivityRange._calc_num_rows(self.categorised_transactions, periods)

        super().__init__(
            top_left_cell,
            self.num_rows,
            self.NUM_COLUMNS
        )
        self.accounting_activity: AccountingActivity = checked_type(accounting_activity, AccountingActivity)
        self.periods: List[DateRange] = checked_list_type(periods, DateRange)

    def format_requests(self):
        reqs = [
                   self.outline_border_request(),
                   self[0].set_bold_text_request(),
                   self[0].border_request(["bottom"]),
                   self[-1].border_request(["top"]),
                   self[:, 0].set_bold_text_request(),
                   self[:, -1].set_decimal_format_request("#,##0"),
                   self[-1].offset(rows=1).border_request(["top"], style="SOLID_MEDIUM"),
               ] + self._groupings()
        return reqs

    def _groupings(self):
        i_row = 1
        i_first_row = -1
        grouped_rows = []

        for category in self.categorised_transactions.categories:
            category_transactions = self.categorised_transactions.restrict_to_category(category)
            if category_transactions.is_empty:
                continue
            if i_first_row > 0:
                grouped_rows.append((i_first_row, i_row - 1))
            i_row += 1
            i_first_row = i_row
            for period in self.periods:
                period_transactions = category_transactions.restrict_to_period(period)
                if period_transactions.is_empty:
                    continue
                i_row += 1
                if period_transactions.num_transactions > 1:
                    i_row += len(period_transactions.transactions)
        grouped_rows.append((i_first_row, i_row - 1))
        return [
            self.tab.group_rows_request(self.i_first_row + i_first_row, self.i_first_row + i_last_row)
            for i_first_row, i_last_row in grouped_rows
        ]

    @staticmethod
    def _calc_num_rows(categorised_transactions: CategorizedTransactions, periods: List[DateRange]):
        n = 1
        for category in categorised_transactions.categories:
            category_transactions = categorised_transactions.restrict_to_category(category)
            if category_transactions.is_empty:
                continue
            n += 1
            for period in periods:
                period_transactions = category_transactions.restrict_to_period(period)
                if period_transactions.is_empty:
                    continue
                n += 1
                if period_transactions.num_transactions > 1:
                    n += len(period_transactions.transactions)
        n += 1
        return n

    def values(self):
        rows = [
            (self[0], ["Category", "", "", "Period", "Date", "Account", "Payee", "", "", "Amount"]),
        ]
        i_row = 1
        for category in self.categorised_transactions.categories:
            category_transactions = self.categorised_transactions.restrict_to_category(category)
            if category_transactions.is_empty:
                continue
            rows.append(
                (
                    self[i_row],
                    [category or "Uncategorized"] + [""] * 8 + [category_transactions.total_amount]
                )
            )
            i_row += 1
            for period in self.periods:
                period_transactions = category_transactions.restrict_to_period(period)
                if period_transactions.is_empty:
                    continue
                if period_transactions.num_transactions == 1:
                    t = period_transactions.transactions[0]
                    rows.append(
                        (
                            self[i_row],
                            ["", "", "", period, t.payment_date, t.account.name, t.payee, "", "", t.amount]
                        )
                    )
                    i_row += 1
                else:
                    rows.append(
                        (
                            self[i_row],
                            ["", "", ""] + [period] + [""] * 5 + [period_transactions.total_amount]
                        )
                    )
                    i_row += 1
                    sorted_transactions = sorted(
                        period_transactions.transactions,
                        key=lambda t: (t.payment_date, t.account.name, t.payee)
                    )
                    for t in sorted_transactions:
                        rows.append(
                            (
                                self[i_row],
                                [""] * 4 + [t.payment_date, t.account.name, t.payee, "", "", t.amount]
                            )
                        )
                        i_row += 1
        rows.append(
            (self[-1], ["Total", "", "", "", "", "", "", "", "", self.categorised_transactions.total_amount]),
        )
        return rows
