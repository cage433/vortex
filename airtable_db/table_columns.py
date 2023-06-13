from enum import Enum


class TicketCategory(Enum):
    ONLINE = 1
    WALK_IN = 2


class TicketPriceLevel(Enum):
    FULL = 1
    MEMBER = 2
    CONCESSION = 3
    OTHER = 4


class EventColumns:
    EVENT_ID = "Record ID"
    SHEETS_EVENT_TITLE = "SheetsEventTitle"
    EVENT_DATE = "Event Date"
    DOORS_TIME = "Doors Time"
    SOUND_ENGINEER = "Sound Engineer"
    NIGHT_MANAGER_NAME = "Night Manager Name"
    VOL_1 = "Vol 1 Name"
    VOL_2 = "Vol 2 Name"
    VOL_3 = "Vol 3 Name"
    STATUS = "Status"
    MEMBER_BOOKINGS = "Member Bookings"
    NM_NOTES = "NM Notes"
    FULL_PRICE_TICKETS_ONLINE = "Full price tickets (online)"
    FULL_PRICE_TICKETS_WALK_IN = "Full price tickets (walk-in)"
    FULL_PRICE_SALES = "Full price sales"
    MEMBER_TICKETS_ONLINE = "Member tickets (online)"
    MEMBER_TICKETS_WALK_IN = "Member tickets (walk-in)"
    STUDENT_TICKETS_ONLINE = "Student tickets (online)"
    STUDENT_TICKETS_WALK_IN = "Student tickets (walk-in)"
    STUDENT_SALES = "Student sales"
    PROMO_TICKETS = "Promo tickets (free)"
    MEMBER_PRICE = "Member ticket price"
    MEMBER_SALES = "Member sales"
    STUDENT_PRICE = "Student ticket price"
    TOTAL_TICKET_SALES = "Total ticket sales"
    OTHER_TICKETS_WALK_IN = "Other tickets (walk-in)"
    OTHER_TICKET_SALES = "Other ticket sales"
    CREDIT_CARD_TAKINGS = "Bar takings"
    EVENING_PURCHASES = "Evening purchases"
    CONTRACT_TYPE = "Contract Type"
    HIRE_FEE = "Hire fee"

    @staticmethod
    def num_tickets_column(category: TicketCategory, price_level: TicketPriceLevel):
        category_text = "online" if category == TicketCategory.ONLINE else "walk-in"
        price_level_text = {
            TicketPriceLevel.FULL: "Full price",
            TicketPriceLevel.MEMBER: "Member",
            TicketPriceLevel.CONCESSION: "Student",
            TicketPriceLevel.OTHER: "Other"
        }
        return f"{price_level_text[price_level]} tickets ({category_text})"

    @staticmethod
    def sales_override_column(price_level: TicketPriceLevel):
        price_level_text = {
            TicketPriceLevel.FULL: "Full price",
            TicketPriceLevel.MEMBER: "Member",
            TicketPriceLevel.CONCESSION: "Student",
        }
        return f"{price_level_text[price_level]} sales override"

class ContractsColumns:
    CODE = "Code"
    RECORD_ID = "Record ID"
    EVENT_TITLE = "Event title"
    EVENTS_LINK = "Events Link"
    ORGANISERS = "Organisers"
    TYPE = "Type"
    STATUS = "Status"
    LIVE_PAYABLE = "Live Payable"
    VORTEX_PROFIT = "Vortex Profit"
    HIRE_FEE = "Hire fee"
    FOOD_BUDGET = "Food budget"
    COS_REQUIRED = "COS required"
    TOTAL_TICKET_SALES_CALC = "Total Ticket Sales £ calc"
    PERFORMANCE_DATE = "Performance date"

    B_ONLINE = "B - Online"
    C_CARD = "C - Card"
    D_CASH = "D - Cash"
    E_STUDENTS = "E - Students"
    N_CREDIT_CARD_TAKINGS = "N - Credit card takings"
    DEDUCTIONS = "Deductions"
    TOTAL_AUDIENCE = "Total audience"
    HOTEL = "Hotel?"
    HOTELS_COST = "Hotels cost"
    TRANSPORT = "Transport"
    TRANSPORT_COST = "Transport Cost"
    AUDIENCE_FOOD_COST = "Audience Food Cost "
    PRS_PAYABLE = "PRS?"
    PAID = "Paid?"
    NIGHT_MANAGER = "Night Manager"
    GRANTS = "Grants"

    FULL_TICKET_PRICE = "Full ticket price"
    MEMBER_TICKET_PRICE = "Member ticket price"
    STUDENT_TICKET_PRICE = "Student ticket price"
    MUSICIANS_FEE = "Musicians fee"

    @staticmethod
    def ticket_price_column(price_level: TicketPriceLevel):
        price_level_text = {
            TicketPriceLevel.FULL: "Full ticket price",
            TicketPriceLevel.MEMBER: "Member ticket price",
            TicketPriceLevel.CONCESSION: "Student ticket price",
        }
        return price_level_text[price_level]


