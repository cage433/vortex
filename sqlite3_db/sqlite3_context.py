import sqlite3

from utils import checked_type


class Sqlite3:
    def __init__(self, file: str):
        self.file: str = checked_type(file, str)

    def __enter__(self):
        self.conn = sqlite3.connect(self.file)
        self.conn.row_factory = sqlite3.Row
        return self.conn.cursor()

    def __exit__(self, type, value, traceback):
        self.conn.commit()
        self.conn.close()