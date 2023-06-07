from datetime import datetime

__all__ = ["parse_date"]

def parse_date(text):
    formats = [
        "%Y-%m-%d",
        "%d-%b-%y",
        "%d-%b-%Y",
        "%d-%m-%y",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%d %b %y",
        "%Y-%b-%d",
        "%Y%m%d",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(text.strip(), fmt).date()
        except ValueError:
            pass
    raise ValueError(f"Can't parse '{text}' as date")
