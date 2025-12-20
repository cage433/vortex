from typing import Optional

from bank_statements import Transaction
from bank_statements.bank_account import ALL_BANK_ACCOUNTS
from bank_statements.payee_categories import PayeeCategory, MUSICIANS
from date_range import Day


def matches_start(transaction, matches: any) -> bool:
    if isinstance(matches, str):
        matches = [matches]
    payee = transaction.payee.lower()
    for match in matches:
        if payee.startswith(match):
            return True
    return False


def matches_end(transaction, matches: any) -> bool:
    if isinstance(matches, str):
        matches = [matches]
    payee = transaction.payee.lower()
    for match in matches:
        if payee.endswith(match):
            return True
    return False


def matches_anywhere(transaction, matches: any) -> bool:
    if isinstance(matches, str):
        matches = [matches]
    payee = transaction.payee.lower()
    for match in matches:
        if match in payee:
            return True
    return False


def _maybe_work_permit(transaction: Transaction) -> Optional[PayeeCategory]:
    if matches_anywhere(
            transaction,
            [
                "ukvi uk",
                "ukvi crewe",
                "hingwan k c cos",
                "mr j hill vjc cos",
                "frusion media acco cos",
                "klarna*cos",
                "klarna*www",
                "ukba",
            ],
    ):
        return PayeeCategory.WORK_PERMITS
    payee = transaction.payee
    if transaction.payment_date == Day(2022, 5, 20) and "K HINGWAN VORTEX EXPENSESS" in payee:
        return PayeeCategory.WORK_PERMITS
    if transaction.payment_date == Day(2022, 11, 2) and "DUSTY KNUC" in payee:
        return PayeeCategory.WORK_PERMITS


def _maybe_rates(transaction: Transaction) -> Optional[PayeeCategory]:
    if matches_anywhere(transaction, ["lb hackney rates", "lbh rates", "l.b. hackney nndr"]):
        return PayeeCategory.RATES


def _maybe_electricity(transaction: Transaction) -> Optional[PayeeCategory]:
    if matches_anywhere(transaction, "edf energy"):
        return PayeeCategory.ELECTRICITY


def _maybe_equipment_costs(transaction: Transaction) -> Optional[PayeeCategory]:
    if matches_start(transaction, ["gear4music", "www.studiospares"]):
        return PayeeCategory.EQUIPMENT_PURCHASE
    if matches_anywhere(transaction, "www.thomann.de burgebrach"):
        return PayeeCategory.EQUIPMENT_PURCHASE
    if matches_anywhere(transaction, "get hire ltd"):
        return PayeeCategory.EQUIPMENT_HIRE


def _maybe_insurance(transaction: Transaction) -> Optional[PayeeCategory]:
    if matches_start(
            transaction,
            [
                "close-jelf",
                "close - marshcomm",
                "axa insurance"
            ]):
        return PayeeCategory.INSURANCE


def _maybe_internal_transfer(transaction: Transaction) -> Optional[PayeeCategory]:
    for acc in ALL_BANK_ACCOUNTS:
        if matches_anywhere(transaction, f"{acc.id} internet transfer"):
            return PayeeCategory.INTERNAL_TRANSFER


def _maybe_kashflow(transaction: Transaction) -> Optional[PayeeCategory]:
    if matches_anywhere(transaction, "www.kashflow.com"):
        return PayeeCategory.KASHFLOW


def _maybe_cc_fees(transaction: Transaction) -> Optional[PayeeCategory]:
    if matches_anywhere(transaction, "pas re cps"):
        return PayeeCategory.CREDIT_CARD_FEES


def _maybe_bb_loan(transaction: Transaction) -> Optional[PayeeCategory]:
    if matches_start(transaction, "loan"):
        return PayeeCategory.BB_LOAN
    if matches_anywhere(transaction, " loan"):
        return PayeeCategory.BB_LOAN


def _maybe_petty_cash(transaction: Transaction) -> Optional[PayeeCategory]:
    if matches_anywhere(transaction, ["cash halifax", "cash hsbc"]):
        return PayeeCategory.PETTY_CASH
    if matches_start(transaction, "cash notemac"):
        return PayeeCategory.PETTY_CASH


def _maybe_bank_fees(transaction: Transaction) -> Optional[PayeeCategory]:
    if matches_anywhere(
            transaction,
            [
                "non-sterling transaction fee",
                "charge renewal fee",
                "total charges to",
                "paytek admin",
            ]

    ):
        return PayeeCategory.BANK_FEES

    if matches_end(transaction, "payment charge"):
        return PayeeCategory.BANK_FEES


def _maybe_bank_interest(transaction: Transaction) -> Optional[PayeeCategory]:
    if matches_anywhere(transaction, "interest to"):
        return PayeeCategory.BANK_INTEREST


def _maybe_salaries(transaction: Transaction) -> Optional[PayeeCategory]:
    if matches_start(
            transaction,
            [
                "pauline le divenac",
                "daniel garel",
                "kim macari",
                "tea earle",
                "ted mitchell",
                "k hingwan vortex",
                "chloe xiao",
                "hector tejero"
            ]

    ):
        return PayeeCategory.SALARIES


def _maybe_memberships(transaction: Transaction) -> Optional[PayeeCategory]:
    if transaction.amount > 0:
        if matches_anywhere(transaction, "stripe") and not matches_anywhere(transaction, "mushroom"):
            return PayeeCategory.MEMBERSHIPS
        if matches_anywhere(transaction, ["chinekwu", "membership"]):
            return PayeeCategory.MEMBERSHIPS


def _maybe_card_sales(transaction: Transaction) -> Optional[PayeeCategory]:
    if matches_anywhere(transaction, "paypal ppwdl"):
        return PayeeCategory.CARD_SALES
    if matches_anywhere(transaction, "rails ltd butlr"):
        return PayeeCategory.CARD_SALES


def _maybe_cash_sales(transaction: Transaction) -> Optional[PayeeCategory]:
    if matches_anywhere(transaction, "cash in p.o."):
        return PayeeCategory.CASH_SALES


def _maybe_ticket_sales(transaction: Transaction) -> Optional[PayeeCategory]:
    if transaction.amount > 0 and matches_start(transaction, ["ticketweb uk", "ticketco uk", "tw client gbp"]):
        return PayeeCategory.TICKET_SALES


def _maybe_bar_purchases(transaction: Transaction) -> Optional[PayeeCategory]:
    if matches_start(
            transaction,
            [
                "drinksuper",
                "dalston local",
                "east london brew",
                "flint wines",
                "humble grape",
                "london beer gas",
                "london gases",
                "majestic wine",
                "newcomer wines",
                "sainsbury",
                "food & wine"
            ]

    ):
        return PayeeCategory.BAR_STOCK


def _maybe_gig_security(transaction: Transaction) -> Optional[PayeeCategory]:
    if matches_start(transaction, "denise williams"):
        return PayeeCategory.GIG_SECURITY


def _maybe_fire_alarm(transaction: Transaction) -> Optional[PayeeCategory]:
    if matches_start(transaction, "agf fire prot"):
        return PayeeCategory.FIRE_ALARM


def _maybe_vat(transaction: Transaction) -> Optional[PayeeCategory]:
    if matches_start(transaction, "hmrc vat"):
        return PayeeCategory.VAT


def _maybe_cleaning(transaction: Transaction) -> Optional[PayeeCategory]:
    if matches_start(transaction, "poolfresh"):
        return PayeeCategory.CLEANING
    if matches_start(transaction, "direct 365"):
        return PayeeCategory.CLEANING


def _maybe_donation(transaction: Transaction) -> Optional[PayeeCategory]:
    if matches_anywhere(transaction, "crowdfunder"):
        return PayeeCategory.DONATION


def _maybe_piano_tuner(transaction: Transaction) -> Optional[PayeeCategory]:
    if matches_start(transaction, ["b sharp pianos", "dafydd james", "d r james"]):
        return PayeeCategory.PIANO_TUNER


def _maybe_sound_engineer(tr: Transaction) -> Optional[PayeeCategory]:
    if tr.amount > 0:
        return None

    known_engineers = [
        "adrian kunstler",
        "ali ward",
        "andrei eliade",
        "andrew marriott",
        "bella cooper",
        "chris penty",
        "delphi mangan",
        "d j tucker",
        "egglectic",
        "felix threadgill",
        "giulo matheson",
        "giulio matheson",
        "jeremy sliwerski",
        "joe mashiter",
        "jorge martinez",
        "kinga ilyes",
        "lauren shapiro",
        "laura kazaroff",  # On behalf of Mike O'Malley
        "louis huddle",
        "mike omalley",
        "mike o'malley",
        "milo mcguire",
        "ochuko okiemute",
        "thomas pew",
    ]
    if matches_start(tr, known_engineers):
        return PayeeCategory.SOUND_ENGINEER


def _maybe_prs(tr: Transaction) -> Optional[PayeeCategory]:
    if matches_start(tr, ["prs ", "pannone "]):
        return PayeeCategory.PRS


def _maybe_mailchimp(tr: Transaction) -> Optional[PayeeCategory]:
    if matches_anywhere(tr, "mailchi"):
        return PayeeCategory.MAILCHIMP


def _maybe_host(tr: Transaction) -> Optional[PayeeCategory]:
    if matches_start(tr, "oblong"):
        return PayeeCategory.WEB_HOST


def _maybe_bt(tr: Transaction) -> Optional[PayeeCategory]:
    if matches_start(tr, "bt group"):
        return PayeeCategory.BT


def _maybe_slack(tr: Transaction) -> Optional[PayeeCategory]:
    payee = tr.payee.lower()
    if payee.startswith("int") and "slack" in payee:
        return PayeeCategory.SLACK


def _maybe_bar_snacks(tr: Transaction) -> Optional[PayeeCategory]:
    if matches_start(tr, "uk bar snacks"):
        return PayeeCategory.BAR_SNACKS


def _maybe_airtable(tr: Transaction) -> Optional[PayeeCategory]:
    payee = tr.payee.lower()
    if payee.startswith("int") and "airtable" in payee:
        return PayeeCategory.AIRTABLE


def _maybe_accountant(tr: Transaction) -> Optional[PayeeCategory]:
    if matches_start(tr, "ck partnership"):
        return PayeeCategory.ACCOUNTANT


def _maybe_musician_payments(tr: Transaction) -> Optional[PayeeCategory]:
    payee = tr.payee.lower()
    if tr.amount < 0:
        for m in MUSICIANS:
            if payee.startswith(m):
                return PayeeCategory.MUSICIAN_PAYMENTS
            if m in payee and "new vortex jazz" in payee:
                return PayeeCategory.MUSICIAN_PAYMENTS
            if m in payee and payee.startswith("vortex"):
                return PayeeCategory.MUSICIAN_PAYMENTS


def _maybe_mvt(tr: Transaction) -> Optional[PayeeCategory]:
    if matches_start(tr, "music venue trust"):
        return PayeeCategory.MUSIC_VENUE_TRUST


def _maybe_tissues(tr: Transaction) -> Optional[PayeeCategory]:
    if matches_start(tr, ["nisbets", "nisa local", "krystal", "acme catering"]):
        return PayeeCategory.OPERATIONAL_COSTS
    if matches_start(tr, ["amznmktplace", "argos ltd", "krys-"]) and 0 > tr.amount > -200:
        return PayeeCategory.OPERATIONAL_COSTS
    if matches_anywhere(tr, ["www.amazon", "marks & spencer", "canva* "]) and 0 > tr.amount > -200:
        return PayeeCategory.OPERATIONAL_COSTS


def _maybe_telephone(tr: Transaction) -> Optional[PayeeCategory]:
    if matches_start(tr, "studio upstairs"):
        return PayeeCategory.TELEPHONE
    if matches_anywhere(tr, "british telecom"):
        return PayeeCategory.TELEPHONE


def _maybe_building_maintenance(tr: Transaction) -> Optional[PayeeCategory]:
    maintainers = [
        "rentokil", "locksmiths", "vivid lifts",
        "upney electrical", "ths electrical", "jar mechanical",
        "a c kemp", "sango air con", "unknown works ltd",
        "j & c joel", "vortex interiors", "h2 catering"
    ]
    if any(matches_anywhere(tr, maintainer) for maintainer in maintainers):
        return PayeeCategory.BUILDING_MAINTENANCE


def _maybe_musician_costs(tr: Transaction) -> Optional[PayeeCategory]:
    if matches_anywhere(tr, [
        "premier cars",
        "kingslandlocke",
        "eagle mini cabs",
        "www.staycity.com",
        "staycity group",
        "avo hotel",
        "global lodge",
        "premier inn",
    ]):
        return PayeeCategory.MUSICIAN_COSTS
    if matches_start(tr, "eurostar"):
        return PayeeCategory.MUSICIAN_COSTS


def _maybe_operational_costs(tr: Transaction) -> Optional[PayeeCategory]:
    if matches_start(
            tr,
            [
                "post office",
                "postoffice",
                "leyland",
                "krystal",
                "dalston stationers",
                "www.nisbets.com",
                "lb hackney genfund"  # Hackney Council, bin collection
            ]):
        return PayeeCategory.OPERATIONAL_COSTS

    if matches_anywhere(tr, ["shopify", "amazon"]) and -50.0 < tr.amount < 0.0:
        return PayeeCategory.OPERATIONAL_COSTS


def _maybe_rent(tr: Transaction) -> Optional[PayeeCategory]:
    if matches_start(tr, "hcd vortex rent"):
        return PayeeCategory.RENT


def _maybe_license_renewal(tr: Transaction) -> Optional[PayeeCategory]:
    if matches_start(tr, "hackney.gov.uk"):
        return PayeeCategory.LICENSING


def _maybe_building_security(tr: Transaction) -> Optional[PayeeCategory]:
    if matches_start(tr, ["adt inv", "adt fire", "adt leeds", "fowler fire"]):
        return PayeeCategory.BUILDING_SECURITY


def _maybe_space_hire(tr: Transaction) -> Optional[PayeeCategory]:
    if tr.amount > 0:
        hirers = [
            "allsopp j",
            "arisema tekle",
            "berahab",
            "blow the fuse",
            "c sansom",
            "chalk oliver",
            "cheng xie",
            "city of london",
            "costley-white",
            "david miller",
            "daytime hire",
            "derick downstairs",
            "derick foodbar",
            "derick rent",
            "duke street",
            "e l rossi",
            "eastmond",
            "elaine mitchener",
            "emma rawicz",
            "frank nancy",
            "future sounds",
            "ghosh a k",
            "intothe void",
            "jewish music",
            "lise rossi",
            "m b dunlop",
            "mcloughlin d",
            "n charles",
            "olivia murphy",
            "rayner a",
            "rehears",
            "rehersal",
            "samuel glass",
            "state of tru",
            "tots tunes",
            "vice uk",
            "vortex jazz jazz connect",
            "w g b marrows",
            "yazz ahmed",
        ]
        if matches_anywhere(tr, hirers):
            return PayeeCategory.SPACE_HIRE
        if matches_anywhere(tr, "mushroom") and matches_anywhere(tr, "stripe"):
            return PayeeCategory.SPACE_HIRE
        return None
    return None


def _maybe_subscriptions(tr: Transaction) -> Optional[PayeeCategory]:
    if matches_start(tr, ["music venues allia wimborne", "jazz in london vortex"]):
        return PayeeCategory.SUBSCRIPTIONS


def category_for_transaction(transaction: Transaction) -> PayeeCategory:
    return (_maybe_airtable(transaction) or
            _maybe_accountant(transaction) or
            _maybe_bank_fees(transaction) or
            _maybe_bank_interest(transaction) or
            _maybe_bar_purchases(transaction) or
            _maybe_bar_snacks(transaction) or
            _maybe_bb_loan(transaction) or
            _maybe_bt(transaction) or
            _maybe_building_maintenance(transaction) or
            _maybe_building_security(transaction) or
            _maybe_card_sales(transaction) or
            _maybe_cash_sales(transaction) or
            _maybe_cc_fees(transaction) or
            _maybe_cleaning(transaction) or
            _maybe_donation(transaction) or
            _maybe_electricity(transaction) or
            _maybe_equipment_costs(transaction) or
            _maybe_fire_alarm(transaction) or
            _maybe_gig_security(transaction) or
            _maybe_host(transaction) or
            _maybe_insurance(transaction) or
            _maybe_internal_transfer(transaction) or
            _maybe_kashflow(transaction) or
            _maybe_license_renewal(transaction) or
            _maybe_mailchimp(transaction) or
            _maybe_memberships(transaction) or
            _maybe_musician_costs(transaction) or
            _maybe_musician_payments(transaction) or
            _maybe_mvt(transaction) or
            _maybe_operational_costs(transaction) or
            _maybe_petty_cash(transaction) or
            _maybe_piano_tuner(transaction) or
            _maybe_prs(transaction) or
            _maybe_rates(transaction) or
            _maybe_rent(transaction) or
            _maybe_salaries(transaction) or
            _maybe_slack(transaction) or
            _maybe_sound_engineer(transaction) or
            _maybe_space_hire(transaction) or
            _maybe_subscriptions(transaction) or
            _maybe_telephone(transaction) or
            _maybe_ticket_sales(transaction) or
            _maybe_tissues(transaction) or
            _maybe_vat(transaction) or
            _maybe_work_permit(transaction) or
            PayeeCategory.UNCATEGORISED
            )
