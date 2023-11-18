from airtable_db.members_db import MembersTable
from env import MEMBERS_SPREADSHEET_ID
from google_sheets import Workbook
from google_sheets.members.members_tab import MembersTab


def update_sheet():
    tab = MembersTab(Workbook(MEMBERS_SPREADSHEET_ID))
    tab_members = tab.members_from_tab()
    db_members = MembersTable().get_all_members()
    tab_members_set = set(tab_members)
    db_members_set = set(db_members)
    if tab_members_set != db_members_set:
        print("Updating sheet")
        tab.update(db_members)
    else:
        print("No update needed")


if __name__ == '__main__':
    update_sheet()
