from pathlib import Path

from env import BANK_ACCOUNT_DATA, ACCOUNT_MAPPING_TABLE
from tims_sheets.account_mapping_table import AccountMappingItem, AccountMappingTable
from tims_sheets.bank_account_data import BankAccountData
from utils import checked_dict_type, checked_type


class CategorisedPayee:
    def __init__(self, payee: str, category: AccountMappingItem):
        self.payee: str = checked_type(payee, str)
        self.category: str = checked_type(category, AccountMappingItem)


class PayeeCategories:
    def __init__(self, items: list[CategorisedPayee]):
        self.items_by_payee: dict[str, CategorisedPayee] = {}
        for item in items:
            if item.payee in self.items_by_payee:
                raise ValueError(f"Duplicate payee: {item.payee}")
            self.items_by_payee[item.payee] = item

    @staticmethod
    def from_tims_spreadsheets(bank_account_data: Path = BANK_ACCOUNT_DATA, mapping_table: Path = ACCOUNT_MAPPING_TABLE):
        bank_account_data = BankAccountData.from_spreadsheet(bank_account_data)
        mapping_table = AccountMappingTable.from_spreadsheet(mapping_table)