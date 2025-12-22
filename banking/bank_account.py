from env import CURRENT_ACCOUNT_ID, SAVINGS_ACCOUNT_ID, BBL_ACCOUNT_ID, CHARITABLE_ACCOUNT_ID
from utils import checked_type


class BankAccount:
    def __init__(self, name: str, id: int):
        self.name = checked_type(name, str)
        self.id = checked_type(id, int)

    def __str__(self):
        return f"{self.name} ({self.id})"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

    @staticmethod
    def account_for_id(id: int) -> 'BankAccount':
        for acc in [
            CURRENT_ACCOUNT,
            SAVINGS_ACCOUNT,
            BBL_ACCOUNT,
            CHARITABLE_ACCOUNT,
        ]:
            if acc.id == id:
                return acc
        raise ValueError(f"Unrecognized account id {id}")

    @staticmethod
    def from_name(name: str) -> 'BankAccount':
        for acc in [
            CURRENT_ACCOUNT,
            SAVINGS_ACCOUNT,
            BBL_ACCOUNT,
            CHARITABLE_ACCOUNT,
        ]:
            if acc.name.lower() == name.lower():
                return acc
        raise ValueError(f"Unrecognized account name {name}")

CURRENT_ACCOUNT = BankAccount("Current", CURRENT_ACCOUNT_ID)
SAVINGS_ACCOUNT = BankAccount("Savings", SAVINGS_ACCOUNT_ID)
BBL_ACCOUNT = BankAccount("BBL", BBL_ACCOUNT_ID)
CHARITABLE_ACCOUNT = BankAccount("Charitable", CHARITABLE_ACCOUNT_ID)

ALL_BANK_ACCOUNTS = [
    CURRENT_ACCOUNT,
    SAVINGS_ACCOUNT,
    BBL_ACCOUNT,
    CHARITABLE_ACCOUNT,
]




