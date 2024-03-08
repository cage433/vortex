from pathlib import Path

from date_range.accounting_month import AccountingMonth
from date_range.accounting_year import AccountingYear
from env import TIMS_GIG_REPORTS


def tims_gig_report_sheet_path(month: AccountingMonth) -> Path:
    month_name = month.corresponding_calendar_month.first_day.date.strftime("%b %Y")
    return TIMS_GIG_REPORTS / f"{month.year.y}" / f"Gig Report Month {month.m}  - {month_name}.xlsx"


def tims_gig_report_sheet_values_path(year: AccountingYear) -> Path:
    month = year.last_accounting_month
    month_name = month.corresponding_calendar_month.first_day.date.strftime("%b %Y")
    return TIMS_GIG_REPORTS / f"{month.year.y}" / f"Gig Report Month {month.m}  - {month_name} values.xlsx"
