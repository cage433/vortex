from numbers import Number
from typing import Optional

from date_range import Day
from utils import checked_type, checked_optional_type


class KashflowInvoice:
    def __init__(
            self,
            issue_date: Day,
            paid_date: Optional[Day],
            reference: str,
            external_reference: Optional[str],
            payment: float,
            vat: Optional[float],
            invoice_type: Optional[str],
            note: Optional[str]
    ):
        self.issue_date: Day = checked_type(issue_date, Day)
        self.paid_date: Optional[Day] = checked_optional_type(paid_date, Day)
        self.reference: str = checked_type(reference, str)
        self.external_reference: Optional[str] = checked_optional_type(external_reference, str)
        self.payment: float = checked_type(payment, Number)
        self.vat: Optional[float] = checked_optional_type(vat, Number)
        self.invoice_type: Optional[str] = checked_optional_type(invoice_type, str)
        self.note: Optional[str] = checked_optional_type(note, str)

    def __eq__(self, other):
        if not isinstance(other, KashflowInvoice):
            return False
        return (
                self.issue_date == other.issue_date and
                self.paid_date == other.paid_date and
                self.reference == other.reference and
                self.external_reference == other.external_reference and
                self.payment == other.payment and
                self.vat == other.vat and
                self.invoice_type == other.invoice_type and
                self.note == other.note
        )