from pathlib import Path

from date_range import Day
from env import KASHFLOW_CSV_DIR
from kashflow.invoice import KashflowInvoice
from kashflow.invoices import KashflowInvoices
from utils.file_utils import read_csv_file


class KashflowCSV:
    @staticmethod
    def latest_activity_csv_file():
        files = list(KASHFLOW_CSV_DIR.glob('*.csv'))
        assert len(files) > 0, f"No kashflow files found in {KASHFLOW_CSV_DIR}"
        files = sorted(files, key=lambda f: f.stat().st_mtime)
        return files[-1]

    @staticmethod
    def read_activity_csv_file(file: Path):
        rows = read_csv_file(file)
        while rows[0][0] != "CODE":
            rows.pop(0)
        rows.pop(0)

        def to_float(text: str):
            return float(text.replace(",", ""))

        invoices = []
        for row in rows[:-1]:   # last row is a total
            paid_date = None if row[1].strip() == "" or row[1] == '0' else Day.parse(row[1])
            if row[5].strip() == "":
                payment = -to_float(row[6])
            else:
                payment = to_float(row[5])
            if row[7].strip() and row[8].strip() == "":
                vat = None
            elif row[7].strip() == "":
                vat = -to_float(row[8])
            else:
                vat = to_float(row[8])
            invoice_type = None if row[9].strip() == "" else row[9]
            note = None if row[10].strip() == "" else row[9]
            invoice = KashflowInvoice(
                issue_date=Day.parse(row[0]),
                paid_date=paid_date,
                reference=row[2],
                external_reference=None if row[3] == "" else row[3],
                payment=payment,
                vat=vat,
                invoice_type=invoice_type,
                note=note
            )
            invoices.append(invoice)

        return KashflowInvoices(invoices)

    @staticmethod
    def latest_invoices():
        csv_file = KashflowCSV.latest_activity_csv_file()
        return KashflowCSV.read_activity_csv_file(csv_file)

if __name__ == '__main__':
    invoices = KashflowCSV.latest_invoices()
    print(len(invoices))
