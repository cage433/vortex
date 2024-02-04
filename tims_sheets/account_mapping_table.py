import shelve
from pathlib import Path

import pandas as pd

from env import ACCOUNT_MAPPING_TABLE
from myopt.opt import Opt
from tims_sheets.account_mapping_item import AccountMappingItem
from utils import checked_list_type

SHELF = Path(__file__).parent / "_account_mapping.shelf"


class AccountMappingTable:
    def __init__(self, items: list[AccountMappingItem]):
        self.items: list[AccountMappingItem] = checked_list_type(items, AccountMappingItem)
        self._by_tims_description = {item.tims_description.lower(): item for item in items}

    def get_by_tims_description(self, tims_description: str) -> Opt[AccountMappingItem]:
        return Opt.of(self._by_tims_description.get(tims_description.lower()))

    def __len__(self):
        return len(self.items)

    def clean(self) -> 'AccountMappingTable':
        return AccountMappingTable([item.clean() for item in self.items])

    @staticmethod
    def from_spreadsheet(spreadsheet: Path, force: bool, clean: bool = False) -> 'AccountMappingTable':
        with shelve.open(str(SHELF)) as shelf:
            key = "Mapping Table"
            if key not in shelf or force:
                print(f"Rebuilding table, {force}")
                df = pd.read_csv(spreadsheet, header=0)
                items = []
                for _, row in df.iterrows():
                    items.append(AccountMappingItem.from_pandas_row(row, clean=clean))
                shelf[key] = AccountMappingTable(items)
            return shelf[key]


if __name__ == '__main__':
    table = AccountMappingTable.from_spreadsheet(ACCOUNT_MAPPING_TABLE, force=True)
    print(f"Num items = {len(table)}")
