from typing import List

from pyairtable import Table

from airtable_db.airtable_record import AirtableRecord
from airtable_db.table_columns import MembersColumns
from data_objects.member import Member
from date_range import Day
from env import AIRTABLE_TOKEN, MEMBERS_DB_ID
from myopt.opt import Opt


class MembersRecord(AirtableRecord):
    @property
    def first_name(self) -> str:
        return self._airtable_value(MembersColumns.FIRST_NAME, allow_missing=False)

    @property
    def last_name(self) -> str:
        return self._airtable_value(MembersColumns.SECOND_NAME, allow_missing=False)

    @property
    def email(self) -> Opt[str]:
        return Opt.of(self._airtable_value(MembersColumns.EMAIL, allow_missing=True))

    @property
    def membership_type(self) -> str:
        def parse_membership_type(text) -> str:
            upper = text.upper()
            if "DOUBLE" in upper:
                if "CONCESSION" in upper:
                    return "Double Concession"
                return "Double"
            if "CONCESSION" in upper:
                return "Concession"
            if "SINGLE" in upper:
                return "Single"
            if "LIFETIME" in upper:
                return "Lifetime"
            if "STANDARD" in upper:
                return "Single"
            return text

        return Opt.of(self._airtable_value(MembersColumns.MEMBERSHIP_TYPE, allow_missing=True)).map(
            parse_membership_type).get_or_else("Unknown")

    @property
    def start_date(self) -> Day:
        def date_created_text():
            dc_text = self._airtable_value(MembersColumns.DATE_CREATED, allow_missing=False)
            return dc_text[:10]

        date_text = Opt.of(self._airtable_value(MembersColumns.MEMBERSHIP_START_DATE, allow_missing=True)).get_or_else(
            date_created_text()
        )
        return Day.parse(date_text)

    @property
    def expiration_date(self) -> Opt[Day]:
        return Opt.of(self._airtable_value(MembersColumns.EXPIRATION_DATE, allow_missing=True)).map(Day.parse)

    @property
    def cancel_membership(self) -> bool:
        return Opt.of(self._airtable_value(MembersColumns.CANCEL_MEMBERSHIP, allow_missing=True)).map(
            lambda x: x == "cancel").get_or_else(False)

    @property
    def to_member(self) -> Member:
        return Member(
            f"{self.first_name} {self.last_name}",
            self.email,
            self.membership_type,
            self.start_date,
            self.expiration_date,
            self.cancel_membership
        )


class MembersTable:
    TABLE = "Members"

    def __init__(self):
        self.table = Table(AIRTABLE_TOKEN, MEMBERS_DB_ID, MembersTable.TABLE)

    def get_all_members(self) -> List[Member]:
        members = []
        for rec in self.table.all(sort=[MembersColumns.MEMBERSHIP_START_DATE]):
            member = MembersRecord(rec)
            members.append(member.to_member)
        return members


if __name__ == '__main__':
    members = MembersTable().get_all_members()
    print(len(members))
