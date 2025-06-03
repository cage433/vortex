from decimal import Decimal
from typing import Dict, Any

from bank_statements.bank_account import BankAccount
from date_range import Day
from utils import checked_dict_type


class BankBalances:
    def __init__(self, balances: Dict[BankAccount, Dict[Day, Decimal]]):
        self.balances: Dict[BankAccount, Dict[Day, Decimal]] = checked_dict_type(balances, BankAccount, dict)
