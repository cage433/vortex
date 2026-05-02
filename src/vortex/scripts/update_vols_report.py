from collections import defaultdict
from typing import Dict

from env import VOLS_REPORT_ID
from vortex.airtable_db.contracts_table import ContractsTable
from vortex.airtable_db.events_table import EventsTable
from vortex.airtable_db.table_columns import ContractsColumns, EventColumns
from vortex.date_range import Day, DateRange
from vortex.date_range.date_range import SplitType
from vortex.date_range.month import Month
from vortex.date_range.simple_date_range import SimpleDateRange
from vortex.google_sheets import Tab, Workbook
from vortex.google_sheets.tab_range import TabRange


def vols_in_period(period: DateRange) -> Dict[str, int]:
    vol_counts = dict()
    num_events = 0
    num_vols = 0
    for m in period.split_into(Month, SplitType.EXACT):
        e = EventsTable()
        events = e.records_in_range(m, EventColumns.EVENT_ID, EventColumns.SHEETS_EVENT_TITLE,
                                    EventColumns.VOL_1, EventColumns.VOL_2, EventColumns.VOL_3,
                                    EventColumns.PRIMARY_EVENT_TYPE, EventColumns.EVENT_DATE)
        for event in events:
            if event.event_type == "Performance":
                num_events += 1
                for vol in event.vol_names:
                    if vol is not None:
                        num_vols += 1
                        vol_name = vol.lower().replace("(new)", "").strip()
                        vol_counts[vol_name] = vol_counts.get(vol_name, 0) + 1

    return vol_counts


class VolsTab(Tab):
    HEADINGS = ["Name", "Last Month", "Last 3 Months", "Last 6 Months"]

    def __init__(self, workbook: Workbook):
        super().__init__(workbook, "Members")

        self.heading_range = TabRange(self.cell("B2"), num_rows=1, num_cols=len(self.HEADINGS))
        self.members_range = TabRange(
            self.heading_range.bottom_left_cell.offset(num_rows=1, num_cols=0),
            num_rows=500, num_cols=len(self.HEADINGS)
        )


    def update(self, last_month: Dict[str, int], last_three_months: Dict[str, int], last_six_months: Dict[str, int]):
        vols = sorted(list(last_six_months.keys()))
        format_requests = self.clear_values_and_formats_requests() + [
            self.set_column_width_request(0, width=30),
            self.set_column_width_request(1, width=150),
        ]
        format_requests += [
            self.heading_range.outline_border_request(),
            self.heading_range.set_bold_text_request(),
            self.members_range.outline_border_request(),
        ]
        self.workbook.batch_update(format_requests)

        data = []
        for vol in vols:
            data.append([vol, last_month.get(vol, 0), last_three_months.get(vol, 0), last_six_months[vol]])

        self.workbook.batch_update_values([
            (self.heading_range, [self.HEADINGS]),
            (self.members_range, data),
        ])

if __name__ == '__main__':
    m = Day.today().month
    last_six_months = SimpleDateRange((m - 6).first_day, (m + 2).last_day)
    last_three_months = SimpleDateRange((m - 3).first_day, (m + 2).last_day)
    last_month = SimpleDateRange((m - 1).first_day, (m + 2).last_day)
    vol_counts_1 = vols_in_period(last_month)
    vol_counts_3 = vols_in_period(last_three_months)
    vol_counts_6 = vols_in_period(last_six_months)
    vols = sorted(list(vol_counts_1.keys()))
    vols_tab = VolsTab(Workbook(VOLS_REPORT_ID))
    vols_tab.update(vol_counts_1, vol_counts_3, vol_counts_6)
