from myopt.nothing import Nothing
from myopt.opt import Opt
from myopt.something import Something
from utils import checked_type
from utils.type_checks import checked_opt_type


class AccountMappingItem:
    def __init__(
            self,
            tims_description: str,
            level_5: str,
            level_4: Opt[str],
            level_3: Opt[str],
            level_2: Opt[str],
            level_1: Opt[str],
            vat_flag: bool
    ):
        self.tims_description: str = checked_type(tims_description, str)
        self.level_5: str = checked_type(level_5, str)
        self.level_4: Opt[str] = checked_opt_type(level_4, str)
        self.level_3: Opt[str] = checked_opt_type(level_3, str)
        self.level_2: Opt[str] = checked_opt_type(level_2, str)
        self.level_1: Opt[str] = checked_opt_type(level_1, str)
        self.vat_flag: bool = checked_type(vat_flag, bool)

    def clone(
            self,
            level_5 = None,
            level_4=None,
            level_3=None,
            level_2=None,
            level_1=None,
            vat_flag=None,
    ):
        return AccountMappingItem(
            tims_description=self.tims_description,
            level_5=level_5 if level_5 is not None else self.level_5,
            level_4=level_4 if level_4 is not None else self.level_4,
            level_3=level_3 if level_3 is not None else self.level_3,
            level_2=level_2 if level_2 is not None else self.level_2,
            level_1=level_1 if level_1 is not None else self.level_1,
            vat_flag=vat_flag if vat_flag is not None else self.vat_flag,
        )

    def clean(self) -> 'AccountMappingItem':
        item = self
        level_1 = self.level_1.map(lambda s: "Income" if "asset" in s.lower() else s)
        level_2 = self.level_2 \
            .map(lambda s: "Direct" if "dir" in s.lower() else s) \
            .map(lambda s: "Direct" if s == "0" or s == "1" else s) \
            .map(lambda s: "Indirect" if "ind" in s.lower() else s) \
            .map(lambda s: "Loan" if "asset/liability" in s.lower() else s)

        level_3 = self.level_3\
            .map(lambda s: s.capitalize()) \
            .map(lambda s: "Loan" if "loan" in s.lower() else s) \
            .map(lambda s: "Space hire" if "space hire" in s.lower() else s)

        level_4 = self.level_4.map(lambda s: s.capitalize())

        item = item.clone(
            level_1=level_1,
            level_2=level_2,
            level_3=level_3,
            level_4=level_4
        )
        return item

    def category(self, level: int) -> Opt[str]:
        if level == 1:
            return self.level_1
        elif level == 2:
            return self.level_2
        elif level == 3:
            return self.level_3
        elif level == 4:
            return self.level_4
        elif level == 5:
            return Something(self.level_5)
        else:
            raise ValueError(f"Invalid level: {level}")

    @staticmethod
    def from_pandas_row(row, clean: bool = False) -> 'AccountMappingItem':
        def optional_str(cell: any) -> Opt[str]:
            if isinstance(cell, str) and cell.strip() != "":
                return Something(cell)
            return Nothing()

        def clean_level_1(text: str) -> str:
            if not clean:
                return text
            if "asset" in text.lower():
                return "Income"
            return text

        tims_description = str(row["Level 5 (Tim's Description)"])
        item =  AccountMappingItem(
            tims_description=tims_description,
            level_5=tims_description,
            level_4=optional_str(row["Level 4"]),
            level_3=optional_str(row["Level 3"]),
            level_2=optional_str(row["Level 2"]),
            level_1=optional_str(row["Level 1"]),
            vat_flag=bool(row["Vat flag"]),
        )
        if clean:
            item = item.clean()
        return item
