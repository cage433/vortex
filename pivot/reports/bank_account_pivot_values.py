from pivot.pivot_field import PivotField, CategoryField, TimsDescriptionField, TransactionValueField, PayeeField, \
    DateField
from pivot.pivot_value import PivotValue, OptionalStringPivotValue, StringPivotValue, NumericValue, DayPivotValue
from tims_sheets.bank_account_data import BankAccountDataItem
from utils import checked_type

__all__ = ["bank_account_data_item_pivot_value"]

def bank_account_data_item_pivot_value(item: BankAccountDataItem, field: PivotField) -> PivotValue:
    checked_type(item, BankAccountDataItem)
    if isinstance(field, CategoryField):
        value = item.account_mapping_item.flat_map(lambda x: x.category(field.level))
        return OptionalStringPivotValue(value)

    if isinstance(field, TimsDescriptionField):
        return StringPivotValue(item.tims_description)

    if isinstance(field, TransactionValueField):
        return NumericValue(item.transaction)

    if isinstance(field, PayeeField):
        return StringPivotValue(item.payee)

    if isinstance(field, DateField):
        return DayPivotValue(item.day)

    raise ValueError(f"Unexpected field type: {field}")
