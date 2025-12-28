#!/usr/bin/env python3
"""Parse AIMS comboData JSON response and convert to CSV.

This parses the JSON response from the AIMS comboHelpAjax endpoint
and converts it to a CSV file with course information.

Usage:
    python parse_combo_response.py <input.json> <output.csv>
"""

import json
import csv
import sys

def parse_combo_data_to_csv(json_file, csv_file):
    """
    Parse the comboData JSON response and convert it to a CSV file.
    Each entry in comboData has a list of column objects with columnAlias and columnValue.
    """
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    combo_data = data.get('comboData', [])
    total_records = data.get('comboTotalRecordCount', 0)
    
    print(f"Total records: {total_records}")
    print(f"Records in response: {len(combo_data)}")
    
    if not combo_data:
        print("No combo data found!")
        return
    
    # Extract headers from the first record
    headers = []
    for item in combo_data[0].get('list', []):
        column_alias = item.get('columnAlias', '')
        if column_alias:
            headers.append(column_alias)
    
    print(f"Headers: {headers}")
    
    # Extract all rows
    rows = []
    for entry in combo_data:
        row = {}
        for item in entry.get('list', []):
            column_alias = item.get('columnAlias', '')
            column_value = item.get('columnValue', '')
            if column_alias:
                row[column_alias] = column_value
        rows.append(row)
    
    # Write to CSV
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"\nSuccessfully wrote {len(rows)} rows to {csv_file}")
    
    # Print sample of first 3 rows
    print("\nFirst 3 rows preview:")
    for i, row in enumerate(rows[:3]):
        print(f"\nRow {i+1}:")
        for key, value in row.items():
            if value:  # Only print non-empty values
                print(f"  {key}: {value}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <input.json> <output.csv>")
        sys.exit(1)
    
    json_file = sys.argv[1]
    csv_file = sys.argv[2]
    parse_combo_data_to_csv(json_file, csv_file)
