from env import CURRENT_ACCOUNT_ID, SAVINGS_ACCOUNT_ID, BBL_ACCOUNT_ID, CHARITABLE_ACCOUNT_ID
from utils import checked_type


class BankAccount:
    def __init__(self, name: str, id: int):
        self.name = checked_type(name, str)
        self.id = checked_type(id, int)

CURRENT_ACCOUNT = BankAccount("Current", CURRENT_ACCOUNT_ID)
SAVINGS_ACCOUNT = BankAccount("Savings", SAVINGS_ACCOUNT_ID)
BBL_ACCOUNT = BankAccount("BBL", BBL_ACCOUNT_ID)
CHARITABLE_ACCOUNT = BankAccount("Charitable", CHARITABLE_ACCOUNT_ID)




