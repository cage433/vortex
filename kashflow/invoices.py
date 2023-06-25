from typing import Tuple

from date_range import Day
from kashflow.invoice import KashflowInvoice
from utils import checked_list_type
from utils.collection_utils import group_into_dict, single_element


class KashflowInvoices:
    def __init__(self, invoices: list[KashflowInvoice]):
        self.invoices: list[KashflowInvoice] = checked_list_type(invoices, KashflowInvoice)
        self.by_ref_and_issue_date: dict[Tuple[str, Day], list[KashflowInvoice]] = \
            group_into_dict(self.invoices, lambda i: (i.reference, i.issue_date))

    def has_invoice(self, invoice: KashflowInvoice) -> bool:
        return invoice in self.by_ref_and_issue_date.get((invoice.reference, invoice.issue_date), [])

    def __len__(self):
        return len(self.invoices)

    @property
    def earliest_issue_date(self) -> Day:
        return min(i.issue_date for i in self.invoices)

    @property
    def latest_issue_date(self) -> Day:
        return max(i.issue_date for i in self.invoices)