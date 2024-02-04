import csv


def write_csv_file(path, table, quoting = None):
    with open(path, 'wt', newline='') as csvfile:
        writer = csv.writer(csvfile, quoting=quoting)
        writer.writerows(table)


def read_csv_file(path):
    with open(path, 'rt', newline='') as f:
        return list(row for row in csv.reader(f))

