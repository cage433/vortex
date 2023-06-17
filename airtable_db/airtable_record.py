from abc import ABC, abstractmethod


class AirtableRecord(ABC):
    def __init__(self, airtable_rec: dict):
        self.airtable_rec = airtable_rec

    def has_value(self, field: str) -> bool:
        return field in self.airtable_rec['fields']

    def _airtable_value(self, field: str, allow_missing: bool):
        if not allow_missing and field not in self.airtable_rec['fields']:
            raise ValueError(f"Missing field {field} in {self.airtable_rec}")
        return self.airtable_rec['fields'].get(field)

    def column_float_value(self, column: str, allow_missing: bool) -> float:
        return self._airtable_value(column, allow_missing)
