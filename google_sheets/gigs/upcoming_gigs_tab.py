from typing import List

from data_objects.upcoming_gig import UpcomingGig
from google_sheets import Tab, Workbook
from google_sheets.colors import LIGHT_GREEN
from google_sheets.tab_range import TabRange, TabCell


class UpcomingGigsRange(TabRange):
    def __init__(self, top_left_cell: TabCell, num_rows: int):
        super().__init__(top_left_cell, num_rows=num_rows, num_cols=2)


class UpcomingGigsTab(Tab):
    def __init__(
            self,
            workbook: Workbook,
    ):
        super().__init__(workbook, "Upcoming Gigs")
        self.heading_range = TabRange(self.cell("B2"), num_rows=1, num_cols=5)

    def update(self, gigs: List[UpcomingGig]):
        full_range = TabRange(self.heading_range.top_left_cell, num_rows=1 + len(gigs),
                              num_cols=self.heading_range.num_cols)
        format_requests = self.clear_values_and_formats_requests() + [
            self.set_column_width_request(1, width=100),
            self.set_column_width_request(2, width=100),
            self.set_column_width_request(3, width=300),
            self.set_column_width_request(4, width=100),
            self.set_column_width_request(5, width=100),
            self.heading_range.set_bold_text_request(),
            self.heading_range.right_align_text_request(),
            full_range[:, -1].right_align_text_request(),
            full_range[:, 2].left_align_text_request(),
            self.heading_range.background_colour_request(LIGHT_GREEN),
            full_range.outline_border_request(),
        ]
        gigs.sort(key=lambda gig: gig.date)
        month_ranges = []
        i_first_of_month = 0
        for i_gig, gig in enumerate(gigs):
            if gig.date.month != gigs[i_first_of_month].date.month:
                month_ranges.append(
                    TabRange(
                        full_range.top_left_cell.offset(i_first_of_month, 0),
                        num_rows=i_gig - i_first_of_month + 1,
                        num_cols=full_range.num_cols
                    )
                )
                i_first_of_month = i_gig + 1

        for range in month_ranges:
            format_requests.append(range.outline_border_request())

        self.workbook.batch_update(format_requests)

        values = [
            [
                "Month", "Date", "Name", "Door time", "Type",
            ]
        ]
        for i_gig, gig in enumerate(gigs):
            if i_gig == 0 or gig.date.month != gigs[i_gig - 1].date.month:
                month_text = gig.date.month.month_name
            else:
                month_text = ""

            values.append([
                month_text,
                gig.date,
                gig.title,
                gig.door_time.get_or_else(""),
                gig.gig_type.get_or_else(""),
            ])
        gigs_range = TabRange(self.heading_range.top_left_cell, num_rows=1 + len(gigs), num_cols=5)
        self.workbook.batch_update_values([(gigs_range, values)])

