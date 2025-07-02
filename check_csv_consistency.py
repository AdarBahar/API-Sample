import csv
import pandas as pd

CSV_FILE = 'cost_report.csv'

def check_csv_consistency(csv_file):
    with open(csv_file, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            print('CSV file is empty.')
            return
        expected_fields = len(header)
        inconsistent_rows = []
        for i, row in enumerate(reader, start=2):  # start=2 because header is line 1
            if len(row) != expected_fields:
                inconsistent_rows.append((i, row))
        if inconsistent_rows:
            print(f'Found {len(inconsistent_rows)} inconsistent row(s):')
            for line_num, row in inconsistent_rows:
                print(f'  Line {line_num}: {row} (fields: {len(row)})')
        else:
            print('All rows are consistent with the header.')

def main():
    check_csv_consistency(CSV_FILE)
    df = pd.read_csv("cost_report.csv")

if __name__ == '__main__':
    main() 