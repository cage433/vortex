from typing import List

from airtable_db import VortexDB
from airtable_db.contracts_and_events import GigsInfo
from bank_statements import BankActivity
from date_range.accounting_month import AccountingMonth
from date_range.simple_date_range import SimpleDateRange
from kashflow.nominal_ledger import NominalLedger
from utils import checked_type


class AccountingActivity:
    def __init__(self, gigs_info: GigsInfo, nominal_ledger: NominalLedger, bank_activity: BankActivity):
        self.gigs_info: GigsInfo = checked_type(gigs_info, GigsInfo)
        self.nominal_ledger: NominalLedger = checked_type(nominal_ledger, NominalLedger)
        self.bank_activity: BankActivity = checked_type(bank_activity, BankActivity)

    @staticmethod
    def activity_for_months(acc_months: List[AccountingMonth], force: bool) -> 'AccountingActivity':
        gigs_info_list = []

        for month in acc_months:
            month_info = VortexDB().gigs_info_for_period(month, force)
            gigs_info_list += month_info.contracts_and_events

        bounding_period = SimpleDateRange(acc_months[0].first_day, acc_months[-1].last_day)
        gigs_info = GigsInfo(gigs_info_list)
        nominal_ledger = NominalLedger.from_latest_csv_file(force).restrict_to_period(bounding_period)
        bank_activity = BankActivity.build(force).restrict_to_period(bounding_period)
        return AccountingActivity(gigs_info, nominal_ledger, bank_activity)