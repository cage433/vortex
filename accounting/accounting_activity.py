from airtable_db import VortexAirtableDB
from airtable_db.gigs_info import GigsInfo
from bank_statements import BankActivity
from bank_statements.categorized_transaction import CategorizedTransactions
from date_range import DateRange
from date_range.date_range import SplitType
from date_range.month import Month
from google_sheets.statements.statements_tab import StatementsTab
from kashflow.nominal_ledger import NominalLedger
from utils import checked_type


class AccountingActivity:
    def __init__(
            self,
            gigs_info: GigsInfo,
            nominal_ledger: NominalLedger,
            bank_activity: BankActivity,
            current_account_transactions: CategorizedTransactions
    ):
        self.gigs_info: GigsInfo = checked_type(gigs_info, GigsInfo)
        self.nominal_ledger: NominalLedger = checked_type(nominal_ledger, NominalLedger)
        self.bank_activity: BankActivity = checked_type(bank_activity, BankActivity)
        self.current_account_transactions: CategorizedTransactions = checked_type(current_account_transactions,
                                                                                  CategorizedTransactions)

    @staticmethod
    def gig_info_for_period(period: DateRange, force: bool) -> GigsInfo:
        gigs_info_list = []
        for month in period.split_into(Month, SplitType.EXACT):
            month_info = VortexAirtableDB().gigs_info_for_period(month, force)
            gigs_info_list += month_info.contracts_and_events
        return GigsInfo(gigs_info_list)

    @staticmethod
    def activity_for_period(
            period: DateRange,
            force: bool,
            force_bank: bool = False,
            force_nominal_ledger: bool = False,
            force_airtable: bool = False,
            force_transactions: bool = False
    ) -> 'AccountingActivity':

        gigs_info = AccountingActivity.gig_info_for_period(period, force or force_airtable)
        nominal_ledger = NominalLedger.from_latest_csv_file(force or force_nominal_ledger).restrict_to_period(period)
        bank_activity = BankActivity.build(force or force_bank).restrict_to_period(period)
        current_account_transactions = StatementsTab.categorized_transactions(period, force or force_transactions)
        return AccountingActivity(gigs_info, nominal_ledger, bank_activity, current_account_transactions)
