from typing import List

from data_objects.member import Member
from date_range import Day
from google_sheets import Tab, Workbook
from google_sheets.colors import LIGHT_YELLOW, LIGHT_GREEN
from google_sheets.tab_range import TabRange, TabCell
from myopt.nothing import Nothing
from myopt.opt import Opt


class MembersRange(TabRange):
    def __init__(self, top_left_cell: TabCell, num_rows: int):
        super().__init__(top_left_cell, num_rows=num_rows, num_cols=2)


class MembersTab(Tab):
    def __init__(
            self,
            workbook: Workbook,
    ):
        super().__init__(workbook, "Sheet1")
        self.heading_range = TabRange(self.cell("B1"), num_rows=1, num_cols=6)

    def update(self, members: List[Member]):
        full_range = TabRange(self.heading_range.top_left_cell, num_rows=1 + len(members),
                              num_cols=self.heading_range.num_cols)
        format_requests = self.clear_values_and_formats_requests() + [
            self.set_column_width_request(0, width=30),
            self.set_column_width_request(1, width=100),
            self.set_column_width_request(2, width=300),
            self.set_column_width_request(3, width=250),
            self.set_column_width_request(4, width=150),
            self.set_column_width_request(5, width=100),
            self.set_column_width_request(6, width=100),
            self.heading_range.set_bold_text_request(),
            self.heading_range.right_align_text_request(),
            self.heading_range.background_colour_request(LIGHT_GREEN),
            full_range.border_request(["innerHorizontal"]),
            full_range.outline_border_request(),
        ]
        format_requests += [
            self.heading_range.offset(i, 0).background_colour_request(LIGHT_YELLOW)
            for i in range(1, len(members) + 1, 2)
        ]
        self.workbook.batch_update(format_requests)
        values = [
            [
                "Start Date", "Name", "Email", "Type", "Expiration", "Cancelled"
            ]
        ]
        members.sort(key=lambda member: member.start_date)
        for member in reversed(members):
            values.append([
                member.start_date,
                member.name,
                member.email.get_or_else(""),
                member.membership_type,
                member.expiration_date.get_or_else(""),
                member.cancel_membership
            ])
        member_range = TabRange(self.heading_range.top_left_cell, num_rows=1 + len(members), num_cols=6)
        self.workbook.batch_update_values([(member_range, values)])

    def members_from_tab(self) -> List[Member]:
        def to_opt(cell_value):
            if cell_value == "":
                return Nothing()
            return Opt.of(cell_value)

        members = []
        values = self.read_values_for_columns(self.heading_range.columns_in_a1_notation)
        for row in values[1:]:
            start_date = Day.parse(row[0])
            name = row[1]
            email = to_opt(row[2])
            membership_type = row[3]
            expiration = to_opt(row[4]).map(Day.parse)
            cancelled = row[5]
            members.append(Member(
                name,
                email,
                membership_type,
                start_date,
                expiration,
                cancelled.upper() == "TRUE"
            ))
        return members
