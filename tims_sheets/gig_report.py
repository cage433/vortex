import csv
from decimal import Decimal
from numbers import Number
from pathlib import Path
from typing import Dict, TypeVar, Generic, List

import numpy as np
import pandas as pd
from tabulate import tabulate

from date_range.accounting_month import AccountingMonth
from date_range.accounting_year import AccountingYear
from date_range.week import Week
from myopt.nothing import Nothing
from myopt.opt import Opt
from utils.file_utils import write_csv_file
from utils.type_checks import checked_opt_type, checked_type, checked_list_type, checked_dict_type

T = TypeVar("T", bound=Number)


class WeeklyBreakdown(Generic[T]):
    def __init__(self, term: str, weeks: List[Week], values: List[T], mtd_value, vat_estimate: Opt[T]):
        self.term = checked_type(term, str)
        self.weeks = checked_list_type(weeks, Week)
        self.weekly_values: List[T] = checked_list_type(values, Number)
        self.mtd_value: T = checked_type(mtd_value, Number)
        self.vat_estimate: Opt[T] = checked_opt_type(vat_estimate, Number)

    @property
    def has_inconsistent_mtd_value(self):
        return abs(self.mtd_value - sum(self.weekly_values)) > 0.01


class MonthlyGigReportSheet:
    MONTH = "month"
    WEEK = "week"

    AUDIENCE_NUMBER = "audience number"
    ADVANCE_TICKET_SALES = "advance ticket sales"
    CREDIT_CARD_SALES = "credit card ticket sales"
    CASH_TICKET_SALES = "cash ticket sales"
    TOTAL_TICKET_SALES = "total ticket sales"
    EVENING_HIRE_FEE = "evening hire fee"
    DAY_HIRE = "day hire"
    BAR_TAKINGS = "bar takings"
    TOTAL_INCOME = "total income"
    DEAL_FEE = "deal fee"
    CASH_PAID_TO_MUSICIANS = "j cash paid to musicians"
    MUSICIAN_INTERNET = "musician internet"
    MUSICIAN_FEES = "musician fees"
    ACCOMMODATION = "accommodation"
    TRAVEL = "travel"
    CATERING = "catering"
    EQUIPMENT_HIRE = "equipment hire"
    WORK_PERMITS = "work permits"
    SOUND_ENGINEERING = "sound engineering"
    HIRE_FEES = "hire fees"
    MUSICIAN_COSTS = "musician costs"
    PRS = "prs"
    VOLUNTEER_COSTS = "volunteer costs"
    BAR_CASH_PURCHASES = "bar cash purchases"
    DRINKS_CASH_PURCHASES = "drinks cash purchases"
    DRINKS_BANK = "drinks bank"
    DRINKS_CARD = "drinks card"
    BAR_EXPENDITURE = "bar expenditure"
    SECURITY = "security"
    MARKETING = "marketing"

    TERMS = [
        AUDIENCE_NUMBER,
        ADVANCE_TICKET_SALES,
        CREDIT_CARD_SALES,
        CASH_TICKET_SALES,
        TOTAL_TICKET_SALES,
        EVENING_HIRE_FEE,
        DAY_HIRE,
        BAR_TAKINGS,
        TOTAL_INCOME,
        DEAL_FEE,
        CASH_PAID_TO_MUSICIANS,
        MUSICIAN_INTERNET,
        MUSICIAN_FEES,
        ACCOMMODATION,
        TRAVEL,
        CATERING,
        EQUIPMENT_HIRE,
        WORK_PERMITS,
        SOUND_ENGINEERING,
        HIRE_FEES,
        MUSICIAN_COSTS,
        PRS,
        VOLUNTEER_COSTS,
        BAR_CASH_PURCHASES,
        DRINKS_CASH_PURCHASES,
        DRINKS_BANK,
        DRINKS_CARD,
        BAR_EXPENDITURE,
        SECURITY,
        MARKETING,
    ]

    def __init__(
            self,
            month: AccountingMonth,
            audience_number: WeeklyBreakdown[int],
            breakdowns: List[WeeklyBreakdown[Decimal]],
    ):
        self.month: AccountingMonth = checked_type(month, AccountingMonth)
        self.audience_number = checked_type(audience_number, WeeklyBreakdown)
        self.breakdowns: List[WeeklyBreakdown[Decimal]] = checked_list_type(breakdowns, WeeklyBreakdown)
        self.breakdowns_by_term: Dict[str, WeeklyBreakdown[Decimal]] = {b.term: b for b in breakdowns}

    @staticmethod
    def from_spreadsheet(path: Path, month: AccountingMonth) -> 'MonthlyGigReportSheet':
        def exclude_row(row):
            if row[0] is np.nan:
                return True
            if pd.isna(row[0]):
                return True
            return False

        xls = pd.ExcelFile(path)
        sheet = pd.read_excel(xls, 'Monthly Gig Report', header=None)
        rows = [
            list(row[1])[1:] for row in
            list(sheet.iterrows())
        ]
        rows = [row for row in rows if not exclude_row(row)]
        sheet_as_dict = {row[0].lower(): row[1:] for row in rows}
        mtd_column = sheet_as_dict[MonthlyGigReportSheet.WEEK].index("MTD")
        vat_column = sheet_as_dict[MonthlyGigReportSheet.WEEK].index("VAT estimate")
        weeks = [
            Week(month.year, int(w))
            for w in sheet_as_dict[MonthlyGigReportSheet.WEEK][:-2]
            if int(w) <= month.year.num_weeks  # Blank extra week in Aug 21 report
        ]
        breakdowns = []
        audience_breakdown = None
        for term in MonthlyGigReportSheet.TERMS:
            if term == MonthlyGigReportSheet.WEEK:
                continue
            terms = sheet_as_dict[term]
            week_values = terms[:len(weeks)]
            vat = Nothing()
            mtd_value = terms[mtd_column]
            if terms[vat_column] is not np.nan:
                vat = Opt.of(terms[vat_column])
            breakdown = WeeklyBreakdown(term, weeks, week_values, mtd_value, vat)
            if term == MonthlyGigReportSheet.AUDIENCE_NUMBER:
                audience_breakdown = breakdown
            else:
                breakdowns.append(breakdown)

        return MonthlyGigReportSheet(month, audience_breakdown, breakdowns)


def path_for_accounting_month(month: AccountingMonth) -> Path:
    reports_path = Path(
        "/Users/alex/Dropbox (Personal)/vortex/Tim stuff/memory stick/Gig reports monthly/"
    )
    month_name = month.corresponding_calendar_month.first_day.date.strftime("%b %Y")
    return reports_path / f"{month.year.y}" / f"Gig Report Month {month.m}  - {month_name}.xlsx"


class QuarterBreakdown:
    def __init__(self, term: str, months: List[AccountingMonth], month_values: List[Decimal], qtr_value,
                 vat: Opt[Decimal]):
        self.term = checked_type(term, str)
        self.months = checked_list_type(months, AccountingMonth)
        self.month_values: List[Number] = checked_list_type(month_values, Number)
        self.qtr_value: Number = checked_type(qtr_value, Number)
        self.vat: Opt[Number] = checked_opt_type(vat, Number)

        if self.has_inconsistent_qtr_value:
            raise ValueError(f"Qtr value {self.qtr_value} is inconsistent with month values {self.month_values}")

    @property
    def has_inconsistent_qtr_value(self):
        return abs(self.qtr_value - sum(self.month_values)) > 0.01


class QuarterVatSheet:
    TOTAL_TICKET_SALES = "Total Ticket Sales"
    HIRE_FEE = "Hire Fee"
    DAY_HIRE = "Day hire"
    BAR_TAKINGS = "Bar Takings"
    DOWNSTAIRS = "Downstairs"
    OUTPUTS = [TOTAL_TICKET_SALES, HIRE_FEE, DAY_HIRE, BAR_TAKINGS, DOWNSTAIRS]

    DEAL_FEE = "Deal fee"
    MUSICIANS_CASH = "J Cash paid to musicians"
    MUSICIANS_INTERNET = "Musician internet"
    MUSICIANS_FEES = "Musician Fees"
    ACCOMODATION = "Accommodation"
    TRAVEL = "Travel"
    CATERING = "Catering"
    EQUIPMENT_HIRE = "Equipment Hire"
    WORK_PERMITS = "Work Permits"
    SOUND_ENGINEERING = "Sound Engineering"
    HIRE_FEES = "Hire Fees"
    MUSICIAN_COSTS = "Musician Costs"
    PRS = "PRS"
    VOLUNTEER_COSTS = "Volunteer Costs"
    BAR_CASH_PURCHASES = "Bar cash purchases"
    DRINKS_CASH_PURPOSES = "Drinks cash purchases"
    DRINKS_BANK = "Drinks bank"
    DRINKS_CARD = "Drinks card"
    BAR_EXPENDITURE = "Bar Expenditure"
    SECURITY = "Security"
    MARKETING = "Marketing"
    RENT = "Rent and service charge"
    RATES = "Rates"
    ELECTRICITY = "Electricity"
    TELEPHONE = "Telephone"
    INSURANCE = "Insurance"
    SALARIES = "Salaries"
    STAFF_EXPENSES = "Staff Expenses"
    RENTOKIL = "Rentokil"
    GAS = "Gas"
    WASTE_COLLECTION = "Waste - collection"
    BIN_HIRE = "- bin hire"
    DOOR_SECURITY = "Consolidated - door security"
    ALARM = "Fowlers - alarm"
    DAILY_CLEANING = "Daily cleaning"
    BUILDING_MAINTENANCE = "Building maintenance"
    BUILDING_WORKS = "Building Works"
    DOWNSTAIRS_BUILDING_WORKS = "Downstairs building works"
    STEINWAY = "Steinway"
    PIANO_TUNING = "Piano Tuning"
    EQUIPMENT_PURCHASES = "Equipment Purchases"
    EQUIPMENT_MAINTENANCE = "Equipment maintenance"
    WEBSITE = "Website"
    ACCOUNTING = "Accounting"
    OPERATIONAL_COSTS = "Operational costs"
    LICENSING_INDIRECT = "Licensing Indirect"
    EQUIPMENT_PURCHASE = "Equipment Purchase"
    EVENTS = "Events"
    SUBSCRIPTIONS = "Subscriptons"
    CREDIT_CARD_FEES = "Credit card fees"
    BANK_FEES = "Bank fees"
    THIS_IS_THE_VAT_TO_PAY = "This is the VAT to pay"

    INPUTS_1 = [
        DEAL_FEE, MUSICIANS_CASH, MUSICIANS_INTERNET, MUSICIANS_FEES, ACCOMODATION,
        TRAVEL, CATERING, EQUIPMENT_HIRE, WORK_PERMITS, SOUND_ENGINEERING,
        HIRE_FEES, MUSICIAN_COSTS, PRS, VOLUNTEER_COSTS, BAR_CASH_PURCHASES,
        DRINKS_CASH_PURPOSES, DRINKS_BANK, DRINKS_CARD, BAR_EXPENDITURE, SECURITY,
        MARKETING, RENT, RATES, ELECTRICITY, TELEPHONE, INSURANCE, SALARIES,
        STAFF_EXPENSES, RENTOKIL, GAS, WASTE_COLLECTION, BIN_HIRE, DOOR_SECURITY,
        ALARM, DAILY_CLEANING, BUILDING_MAINTENANCE, STEINWAY, EQUIPMENT_MAINTENANCE, WEBSITE,
        ACCOUNTING, OPERATIONAL_COSTS, EQUIPMENT_PURCHASE, EVENTS, SUBSCRIPTIONS,
        CREDIT_CARD_FEES, BANK_FEES,
    ]
    INPUTS_2 = [
        DEAL_FEE, MUSICIANS_CASH, MUSICIANS_INTERNET, MUSICIANS_FEES, ACCOMODATION,
        TRAVEL, CATERING, EQUIPMENT_HIRE, WORK_PERMITS, SOUND_ENGINEERING,
        HIRE_FEES, MUSICIAN_COSTS, PRS, VOLUNTEER_COSTS, BAR_CASH_PURCHASES,
        DRINKS_CASH_PURPOSES, DRINKS_BANK, DRINKS_CARD, BAR_EXPENDITURE, SECURITY,
        MARKETING, RENT, RATES, ELECTRICITY, TELEPHONE, INSURANCE, SALARIES,
        STAFF_EXPENSES, RENTOKIL, GAS, WASTE_COLLECTION, BIN_HIRE, DOOR_SECURITY,
        ALARM, DAILY_CLEANING, BUILDING_MAINTENANCE,

        # STEINWAY,
        PIANO_TUNING,
        EQUIPMENT_PURCHASES,

        EQUIPMENT_MAINTENANCE, WEBSITE,
        ACCOUNTING, OPERATIONAL_COSTS,

        # EQUIPMENT_PURCHASE,
        LICENSING_INDIRECT,

        EVENTS, SUBSCRIPTIONS,
        CREDIT_CARD_FEES, BANK_FEES,
    ]
    INPUTS_3 = [
        DEAL_FEE, MUSICIANS_CASH, MUSICIANS_INTERNET, MUSICIANS_FEES, ACCOMODATION,
        TRAVEL, CATERING, EQUIPMENT_HIRE, WORK_PERMITS, SOUND_ENGINEERING,
        HIRE_FEES, MUSICIAN_COSTS, PRS, VOLUNTEER_COSTS, BAR_CASH_PURCHASES,
        DRINKS_CASH_PURPOSES, DRINKS_BANK, DRINKS_CARD, BAR_EXPENDITURE, SECURITY,
        MARKETING, RENT, RATES, ELECTRICITY, TELEPHONE, INSURANCE, SALARIES,
        STAFF_EXPENSES, RENTOKIL, GAS, WASTE_COLLECTION, BIN_HIRE, DOOR_SECURITY,
        ALARM, DAILY_CLEANING, BUILDING_MAINTENANCE,

        BUILDING_WORKS,
        STEINWAY,
        # PIANO_TUNING,
        # EQUIPMENT_PURCHASES,

        EQUIPMENT_MAINTENANCE, WEBSITE,
        ACCOUNTING, OPERATIONAL_COSTS,

        EQUIPMENT_PURCHASE,
        # LICENSING_INDIRECT,

        EVENTS, SUBSCRIPTIONS,
        CREDIT_CARD_FEES, BANK_FEES,
    ]

    INPUTS_4 = [
        DEAL_FEE, MUSICIANS_CASH, MUSICIANS_INTERNET, MUSICIANS_FEES, ACCOMODATION,
        TRAVEL, CATERING, EQUIPMENT_HIRE, WORK_PERMITS, SOUND_ENGINEERING,
        HIRE_FEES, MUSICIAN_COSTS, PRS, VOLUNTEER_COSTS, BAR_CASH_PURCHASES,
        DRINKS_CASH_PURPOSES, DRINKS_BANK, DRINKS_CARD, BAR_EXPENDITURE, SECURITY,
        MARKETING, RENT, RATES, ELECTRICITY, TELEPHONE, INSURANCE, SALARIES,
        STAFF_EXPENSES, RENTOKIL, GAS, WASTE_COLLECTION, BIN_HIRE, DOOR_SECURITY,
        ALARM, DAILY_CLEANING, BUILDING_MAINTENANCE, BUILDING_WORKS,

        DOWNSTAIRS_BUILDING_WORKS,

        STEINWAY, EQUIPMENT_MAINTENANCE, WEBSITE, ACCOUNTING, OPERATIONAL_COSTS,
        EQUIPMENT_PURCHASE, EVENTS, SUBSCRIPTIONS, CREDIT_CARD_FEES, BANK_FEES,
    ]

    def __init__(
            self,
            inputs: Dict[str, QuarterBreakdown],
            outputs: Dict[str, QuarterBreakdown],
            amount_owed: float
    ):
        self.inputs = checked_dict_type(inputs, str, QuarterBreakdown)
        self.outputs = checked_dict_type(outputs, str, QuarterBreakdown)
        self.amount_owed = checked_type(amount_owed, float)

    @property
    def total_sales_ex_vat(self) -> float:
        return sum([b.qtr_value for b in self.outputs.values()])

    @property
    def total_sales_vat(self) -> float:
        return sum(
            [b.vat.get_or_else(0.0) for item, b in self.outputs.items() if item != QuarterVatSheet.TOTAL_TICKET_SALES])

    @property
    def total_ticket_sales_ex_vat(self):
        return self.outputs[QuarterVatSheet.TOTAL_TICKET_SALES].qtr_value

    @property
    def vat_partial_exemption(self) -> float:
        all_sales = self.total_sales_ex_vat
        ticket_sales = self.total_ticket_sales_ex_vat
        return (all_sales - ticket_sales) / all_sales

    @property
    def total_purchases_ex_vat(self) -> float:
        return sum([b.qtr_value for b in self.inputs.values()])

    @property
    def drinks_vat_paid(self):
        return sum([
            b.vat.get_or_else(0.0)
            for item, b in self.inputs.items()
            if item in [QuarterVatSheet.DRINKS_BANK, QuarterVatSheet.DRINKS_CARD]
        ])

    @property
    def downstairs_works_vat_paid(self):
        return sum([
            b.vat.get_or_else(0.0)
            for item, b in self.inputs.items()
            if item in [QuarterVatSheet.DOWNSTAIRS_BUILDING_WORKS]
        ])

    @property
    def total_vat_paid(self):
        return sum([
            b.vat.get_or_else(0.0)
            for item, b in self.inputs.items()
            if item not in [QuarterVatSheet.MUSICIANS_FEES, QuarterVatSheet.MUSICIAN_COSTS,
                            QuarterVatSheet.BAR_EXPENDITURE]
        ])

    def vat_owed_using_old_method(self, month: AccountingMonth):
        if month < AccountingMonth(AccountingYear(2023), 5):
            partially_exempt_vat_paid = self.total_vat_paid - self.downstairs_works_vat_paid
            return self.total_sales_vat - partially_exempt_vat_paid * self.vat_partial_exemption - self.downstairs_works_vat_paid
        else:
            return self.total_sales_vat - self.total_vat_paid * self.vat_partial_exemption

    def vat_owed_using_new_method(self, month: AccountingMonth):
        if month < AccountingMonth(AccountingYear(2023), 5):
            partially_exempt_vat_paid = self.total_vat_paid - self.drinks_vat_paid - self.downstairs_works_vat_paid
            return (self.total_sales_vat
                    - partially_exempt_vat_paid * self.vat_partial_exemption
                    - self.drinks_vat_paid
                    - self.downstairs_works_vat_paid)
        else:
            partially_exempt_vat_paid = self.total_vat_paid - self.drinks_vat_paid
            return (self.total_sales_vat
                    - partially_exempt_vat_paid * self.vat_partial_exemption
                    - self.drinks_vat_paid
                    )

    @staticmethod
    def from_spreadsheet(path: Path, month: AccountingMonth) -> 'QuarterVatSheet':
        xls = pd.ExcelFile(path)
        sheet = pd.read_excel(xls, 'VAT', header=None)
        rows = [
            row[1].values
            for row in list(sheet.iterrows())
        ]

        def trim_safe(term):
            if isinstance(term, str):
                return term.strip()
            return term

        headings = [trim_safe(row[0]) for row in rows]

        months = [month - 2, month - 1, month]

        def extract_breakdown(heading, expected_terms):
            breakdown_heading_row = headings.index(heading)
            breakdown_total_row = headings.index("Total", breakdown_heading_row + 1)
            assert breakdown_total_row - breakdown_heading_row - 1 == len(expected_terms), \
                f"Expected {len(expected_terms)} outputs, found {breakdown_total_row - breakdown_heading_row - 1}"

            by_term = {}
            for i in range(breakdown_heading_row + 1, breakdown_total_row):
                row = rows[i]
                term = trim_safe(row[0])
                expected_term = expected_terms[i - breakdown_heading_row - 1]
                if not isinstance(term, str) and np.isnan(term) and expected_term == QuarterVatSheet.RATES:
                    term = QuarterVatSheet.RATES
                assert term.lower() == expected_term.lower(), f"Expected [{expected_term}] at row {i}, found [{term}]"
                vat = row[5]
                if isinstance(vat, Number) and np.isnan(vat):
                    vat = Nothing()
                else:
                    vat = Opt.of(vat)
                breakdown = QuarterBreakdown(
                    expected_term,
                    months,
                    [row[1], row[2], row[3]],
                    row[4],
                    vat,
                )
                by_term[term] = breakdown
            return by_term

        if month < AccountingMonth(AccountingYear(2020), 12):
            expected_inputs = QuarterVatSheet.INPUTS_1
        elif month < AccountingMonth(AccountingYear(2021), 3):
            expected_inputs = QuarterVatSheet.INPUTS_2
        elif month < AccountingMonth(AccountingYear(2021), 12):
            expected_inputs = QuarterVatSheet.INPUTS_1
        elif month < AccountingMonth(AccountingYear(2022), 3):
            expected_inputs = QuarterVatSheet.INPUTS_3
        else:
            expected_inputs = QuarterVatSheet.INPUTS_4

        inputs = extract_breakdown("INPUTS", expected_inputs)
        outputs = extract_breakdown("OUTPUTS", QuarterVatSheet.OUTPUTS)

        amount_owed = None
        for row in rows:
            if len(row) >= 13 and row[9] == QuarterVatSheet.THIS_IS_THE_VAT_TO_PAY:
                amount_owed = row[12]
        assert amount_owed is not None, "Couldn't find amount owed"
        return QuarterVatSheet(inputs, outputs, amount_owed)


if __name__ == '__main__':
    # May 22 omitted drinks VAT entirely
    # Feb 23 didn't apply the full rebate to downstairs works
    table = []
    total_diff = 0.0
    for y in range(2019, 2024):
        for m in [3, 6, 9, 12]:
            month = AccountingMonth(AccountingYear(y), m)
            path = path_for_accounting_month(month)
            gig_report = MonthlyGigReportSheet.from_spreadsheet(path, month)
            vat_report = QuarterVatSheet.from_spreadsheet(path, month)
            vat_reported = vat_report.amount_owed
            old_vat = vat_report.vat_owed_using_old_method(month)
            new_vat = vat_report.vat_owed_using_new_method(month)
            diff = old_vat - new_vat
            row = [month,
                   vat_report.vat_partial_exemption * 100.0,
                   vat_reported,
                   old_vat,
                   new_vat, diff,
                   month < AccountingMonth(AccountingYear(2023), 5)]
            table.append(row)
    print(
        tabulate(
            table,
            headers=["Month", "Partial Exemption", "VAT owed (reported)", "VAT owed (old)",
                     "VAT owed (new)", "Overpayment", "month comp"],
            floatfmt=".2f"
        )
    )
    headers = [
        ["", "", "VAT", "", "", ""],
        ["Month", "Partial Exemption", "Reported", "Old method", "New method", "Overpayment", "month comp"]
    ]
    totals = [["Total"] + [sum(row[i] for row in table) for i in range(1, 6)]]
    write_csv_file(Path("/Users/alex/vat-analysis-1.csv"), headers + table + totals, quoting=csv.QUOTE_NONE)
