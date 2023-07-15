from pathlib import Path
from typing import Optional

from env import TIMS_MAPPING_CSV, BANK_MAPPING_WITH_PAYEE_CSV
from utils import checked_type, checked_optional_type, checked_list_type
from utils.file_utils import read_csv_file


class AccountMapping:
    def __init__(
            self,
            payee: str,
            tims_description: str,
            category1: Optional[str],
            category2: Optional[str],
            category3: Optional[str],
            category4: Optional[str],
    ):
        self.payee = checked_type(payee, str)
        self.tims_description = checked_type(tims_description, str)
        self.category1 = checked_optional_type(category1, str)
        self.category2 = checked_optional_type(category2, str)
        self.category3 = checked_optional_type(category3, str)
        self.category4 = checked_optional_type(category4, str)

    def clone(
            self,
            payee: Optional[str] = None,
            tims_description: Optional[str] = None,
            category1: Optional[str] = None,
            category2: Optional[str] = None,
            category3: Optional[str] = None,
            category4: Optional[str] = None,
    ):
        return AccountMapping(
            payee=payee or self.payee,
            tims_description=tims_description or self.tims_description,
            category1=category1 or self.category1,
            category2=category2 or self.category2,
            category3=category3 or self.category3,
            category4=category4 or self.category4,
        )


class AccountMappingTable:
    def __init__(self, mappings: list[AccountMapping]):
        self.mappings = checked_list_type(mappings, AccountMapping)
        self.mappings_by_payee = {m.payee.lower(): m for m in mappings}

    def get_mapping(self, payee: str) -> Optional[AccountMapping]:
        return self.mappings_by_payee.get(payee.lower())

    def __len__(self):
        return len(self.mappings)

    @staticmethod
    def from_csvs(tims_mapping_csv: Optional[Path] = None,
                  bank_mapping_with_payee_csv: Optional[Path] = None) -> 'AccountMappingTable':
        tims_mapping_csv = tims_mapping_csv or TIMS_MAPPING_CSV
        bank_mapping_with_payee_csv = bank_mapping_with_payee_csv or BANK_MAPPING_WITH_PAYEE_CSV
        tims_rows = read_csv_file(tims_mapping_csv)[2:]
        payee_mapping_rows = read_csv_file(bank_mapping_with_payee_csv)[2:]
        payee_mapping_table = {row[2]: row[3] for row in payee_mapping_rows}

        def _category(text: str):
            if text == "":
                return None
            return text

        mappings_sans_payees = []
        for row in tims_rows:
            tims_description = row[0]
            category1 = _category(row[4])
            category2 = _category(row[3])
            category3 = _category(row[2])
            category4 = _category(row[1])
            mappings_sans_payees.append(AccountMapping(
                payee="",
                tims_description=tims_description,
                category1=category1,
                category2=category2,
                category3=category3,
                category4=category4,
            ))

        mappings_via_tims_description = {m.tims_description.lower(): m for m in mappings_sans_payees}
        mappings_with_payees = []
        for payee, tims_description in payee_mapping_table.items():
            tims_description = tims_description.lower()
            if tims_description in mappings_via_tims_description:
                mapping_sans_payee = mappings_via_tims_description[tims_description]
                mappings_with_payees.append(mapping_sans_payee.clone(payee=payee))

        return AccountMappingTable(mappings_with_payees)

    def has_mapping(self, payee: str) -> bool:
        return payee.lower() in self.mappings_by_payee

    def mapping(self, payee: str) -> Optional[AccountMapping]:
        return self.mappings_by_payee.get(payee.lower())


if __name__ == '__main__':
    table = AccountMappingTable.from_csvs()
    print(len(table))
