from env import CASHFLOW_ANALYSIS_ID
from vortex.airtable_db import VortexAirtableDB
from vortex.banking import BankActivity
from vortex.date_range import Day
from vortex.date_range.date_range import SplitType
from vortex.date_range.month import Month
from vortex.date_range.quarter import Quarter
from vortex.date_range.simple_date_range import SimpleDateRange
from vortex.google_sheets import Workbook
from vortex.google_sheets.analysis.cash_flow_analysis_tab import CashFlowAnalysisTab
from vortex.google_sheets.statements.statements_tab import StatementsTab

def update_tab(first_day: Day, last_day: Day, force: bool):

    period = SimpleDateRange(first_day, last_day)
    periods = period.split_into(Quarter, SplitType.OUTER)
    transactions = StatementsTab.transactions(period, force)
    bank_activity = BankActivity.build(force=force).restrict_to_period(period)
    gigs_info = VortexAirtableDB().gigs_info_for_period(period, force=force)
    tab = CashFlowAnalysisTab(Workbook(CASHFLOW_ANALYSIS_ID), "Nov 2025", periods)
    tab.update(transactions, gigs_info, bank_activity)

if __name__ == '__main__':
    first_day = Month(2021, 10).first_day
    last_day = Month(2025, 11).last_day
    update_tab(first_day, last_day, force=False)
