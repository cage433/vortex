from date_range import Day
from myopt.opt import Opt
from utils import checked_type
from utils.type_checks import checked_opt_type


class Member:
    def __init__(
            self,
            name: str,
            email: Opt[str],
            membership_type: str,
            start_date: Day,
            expiration_date: Opt[Day],
            cancel_membership: bool
    ):
        self.name: str = checked_type(name, str)
        self.email: Opt[str] = checked_opt_type(email, str)
        self.membership_type: str = checked_type(membership_type, str)
        self.start_date: Day = checked_type(start_date, Day)
        self.expiration_date: Opt[Day] = checked_opt_type(expiration_date, Day)
        self.cancel_membership: bool = checked_type(cancel_membership, bool)

    def __hash__(self):
        return hash((self.name, self.email, self.membership_type, self.start_date, self.expiration_date,
                     self.cancel_membership))

    def __eq__(self, other):
        if not isinstance(other, Member):
            return False
        return self.name == other.name and \
            self.email == other.email and \
            self.membership_type == other.membership_type and \
            self.start_date == other.start_date and \
            self.expiration_date == other.expiration_date and \
            self.cancel_membership == other.cancel_membership

    def __str__(self):
        return f"Member({self.name}, {self.email}, {self.membership_type}, {self.start_date}, {self.expiration_date}, {self.cancel_membership})"
