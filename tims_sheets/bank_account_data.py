import shelve
from numbers import Number
from pathlib import Path
from typing import Optional

import pandas

from date_range import Day
from myopt.nothing import Nothing
from myopt.opt import Opt
from tims_sheets.account_mapping_table import AccountMappingItem, AccountMappingTable
from utils import checked_type, checked_list_type
from utils.type_checks import checked_opt_type

SHELF = Path(__file__).parent / "_bank_account_data.shelf"


# Note that the column 'payee' is actually Tim's description. It corresponds to
# the field of that nam in the AccountMappingTable
class BankAccountDataItem:
    def __init__(
            self,
            day: Day,
            payee: str,
            tims_description: str,
            transaction: Number,
            account_mapping_item: Opt[AccountMappingItem],
    ):
        self.day: Day = checked_type(day, Day)
        self.payee: str = checked_type(payee, str)
        self.tims_description: str = checked_type(tims_description, str)
        self.transaction: Number = checked_type(transaction, Number)
        self.account_mapping_item: Opt[AccountMappingItem] = \
            checked_opt_type(account_mapping_item, AccountMappingItem)

    @staticmethod
    def from_pandas_row(row):
        tims_description = str(row["Payee"])
        return BankAccountDataItem(
            day=Day.from_date(row["Date"]),
            payee=str(row["Bank Description"]),
            tims_description=tims_description,
            transaction=row["Transaction"],
            account_mapping_item=Nothing[AccountMappingItem](),
        )

    def with_mapping(self, mapping: AccountMappingTable) -> 'BankAccountDataItem':
        return BankAccountDataItem(
            day=self.day,
            payee=self.payee,
            tims_description=self.tims_description,
            transaction=self.transaction,
            account_mapping_item=mapping.get_by_tims_description(self.tims_description),
        )


class BankAccountData:
    def __init__(self, items: list[BankAccountDataItem]):
        self.items: list[BankAccountDataItem] = checked_list_type(items, BankAccountDataItem)

    def filter_by_date(self, first_day: Optional[Day] = None, last_day: Optional[Day] = None) -> 'BankAccountData':
        if first_day is None:
            first_day = Day(1970, 1, 1)
        if last_day is None:
            last_day = Day(2100, 1, 1)
        return BankAccountData([item for item in self.items if first_day <= item.day <= last_day])

    def with_mapping(self, mapping: AccountMappingTable) -> 'BankAccountData':
        return BankAccountData([item.with_mapping(mapping) for item in self.items])

    @staticmethod
    def from_spreadsheet(
            spreadsheet: Path,
            mapping_table: Optional[AccountMappingTable] = None,
            force: bool = False
    ) -> 'BankAccountData':
        with shelve.open(str(SHELF)) as shelf:
            key = f"Bank Data {mapping_table is not None}"
            if key not in shelf or force:
                df = pandas.read_excel(spreadsheet, sheet_name="Current account", usecols="A:F", skiprows=[1])
                items = []
                for _, row in df.iterrows():
                    item = BankAccountDataItem.from_pandas_row(row, )
                    if mapping_table is not None:
                        item = item.with_mapping(mapping_table)
                    items.append(item)
                shelf[key] = BankAccountData(items)
            return shelf[key]

    def __len__(self):
        return len(self.items)

