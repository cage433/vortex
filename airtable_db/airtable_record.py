from abc import ABC, abstractmethod


class AirtableRecord(ABC):
    def __init__(self, airtable_rec: dict):
        self.airtable_rec = airtable_rec

    def _airtable_value(self, field: str):
        if field not in self.airtable_rec['fields']:
            raise ValueError(f"No field '{field}' in record")
        return self.airtable_rec['fields'][field]
