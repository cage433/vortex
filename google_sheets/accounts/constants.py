from numbers import Number
from typing import List

from date_range import Day, DateRange
from utils import checked_type, checked_list_type

VAT_RATE = 0.2
QUARTERLY_RENT = 9344.72
SERVICE_CHARGE = 594.72
QUARTERLY_RENTOKILL = 463.31
QUARTERLY_WASTE_COLLECTION = 342.88
QUARTERLY_BIN_HIRE_EX_VAT = 62.0 / 1.2
YEARLY_DOOR_SECURITY = 470.0
MONTHLY_FOWLERS_ALARM = 75.0

MONTHLY_RENT = QUARTERLY_RENT / 3
MONTHLY_RENTOKILL = QUARTERLY_RENTOKILL / 3
MONTHLY_WASTE_COLLECTION = QUARTERLY_WASTE_COLLECTION / 3
MONTHLY_BIN_HIRE_EX_VAT = QUARTERLY_BIN_HIRE_EX_VAT / 3
MONTHLY_DOOR_SECURITY = YEARLY_DOOR_SECURITY / 12


class SpecialPayment:
    def __init__(self, payee: str, payment_date: Day, amount: float):
        self.payee: str = checked_type(payee, str)
        self.payment_date: Day = checked_type(payment_date, Day)
        self.amount: float = checked_type(amount, Number)


class SpecialPayments:
    def __init__(self, grants: List[SpecialPayment]):
        self.grants = checked_list_type(grants, SpecialPayment)

    def total_for_period(self, period: DateRange):
        return sum([g.amount for g in self.grants if period.contains_day(g.payment_date)])


GRANTS = SpecialPayments([
    SpecialPayment("Arts Council", Day(2018, 3, 16), 14010.0),
    SpecialPayment("Arts Council", Day(2019, 2, 14), 11208.0),
    SpecialPayment("Arts Council", Day(2019, 8, 15), 2802.0),
    SpecialPayment("Arts Council", Day(2020, 6, 25), 31500.0),
    SpecialPayment("Arts Council", Day(2020, 8, 6), 3500.0),
    SpecialPayment("Arts Council", Day(2020, 11, 30), 117266.0),
    SpecialPayment("Arts Council", Day(2021, 4, 26), 50225.0),
    SpecialPayment("Arts Council", Day(2021, 7, 5), 13029.0),
    SpecialPayment("Boyne Music Festival", Day(2021, 8, 12), 776.0),
    SpecialPayment("LB Hackney", Day(2021, 11, 30), 4800.0),
    SpecialPayment("Arts Council", Day(2021, 12, 1), 50225.0),
    SpecialPayment("LB Hackney", Day(2022, 1, 25), 10000.0),
    SpecialPayment("Arts Council", Day(2022, 3, 15), 21525.0),
    SpecialPayment("LB Hackney", Day(2022, 3, 16), 9100.0),
    SpecialPayment("LB Hackney", Day(2022, 3, 21), 4000.0),
    SpecialPayment("LB Hackney", Day(2022, 4, 1), 214.0),
    SpecialPayment("Arts Council", Day(2022, 4, 21), 36000.0),
    SpecialPayment("Arts Council", Day(2022, 6, 2), 21525.0),
    SpecialPayment("Arts Council", Day(2022, 7, 21), 4000.0)
])


PRS_PAYMENTS = SpecialPayments([
    SpecialPayment("PRS", Day(2023, 4, 17), -11132.6),
    SpecialPayment("PRS", Day(2023, 5, 5), -1565.16),
    SpecialPayment("PRS", Day(2023, 6, 5), -2056.04),
])
INSURANCE_PAYMENTS = SpecialPayments([
    SpecialPayment("Insurance", Day(2023, 9, 20), 18120.0),
])
