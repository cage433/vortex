from airtable_db import VortexDB
from airtable_db.contracts_and_events import GigsInfo
from bank_statements import BankActivity
from date_range import DateRange
from date_range.date_range import SplitType
from date_range.month import Month
from kashflow.nominal_ledger import NominalLedger
from utils import checked_type


class AccountingActivity:
    def __init__(self, gigs_info: GigsInfo, nominal_ledger: NominalLedger, bank_activity: BankActivity):
        self.gigs_info: GigsInfo = checked_type(gigs_info, GigsInfo)
        self.nominal_ledger: NominalLedger = checked_type(nominal_ledger, NominalLedger)
        self.bank_activity: BankActivity = checked_type(bank_activity, BankActivity)

    @staticmethod
    def activity_for_period(period: DateRange, force: bool) -> 'AccountingActivity':
        gigs_info_list = []

        for month in period.split_into(Month, SplitType.EXACT):
            month_info = VortexDB().gigs_info_for_period(month, force)
            gigs_info_list += month_info.contracts_and_events

        gigs_info = GigsInfo(gigs_info_list)
        nominal_ledger = NominalLedger.from_latest_csv_file(force).restrict_to_period(period)
        bank_activity = BankActivity.build(force).restrict_to_period(period)
        return AccountingActivity(gigs_info, nominal_ledger, bank_activity)
