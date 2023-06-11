from abc import ABC, abstractmethod


class AirtableRecord(ABC):
    def __init__(self, airtable_rec: dict):
        self.airtable_rec = airtable_rec

    def has_value(self, field: str) -> bool:
        return field in self.airtable_rec['fields']

    def _airtable_value(self, field: str, default=None):
        if field not in self.airtable_rec['fields']:
            return default
        return self.airtable_rec['fields'][field]

