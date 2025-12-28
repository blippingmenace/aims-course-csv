# AIMS Course Timetable Fetcher

> [!WARNING]
> This repository may not be fully functional. Please contact the repository owner for assistance.

Fetch and process course slot timings from AIMS (Academic Information Management System).

## Overview

This tool helps you:
1. Fetch slot timings for all running courses from AIMS
2. Combine course data with slot information
3. Generate structured outputs for analysis

## Prerequisites

- Python 3.7+
- Access to AIMS portal
- Valid AIMS session cookies

## Setup

### 1. Prepare Course Data

You need to first fetch course data from AIMS to create the initial CSV files.

**Option A: Use Setup Scripts (Recommended)**

The [setup/](setup/) directory contains scripts to fetch course data from AIMS:
- `fetch_courses.sh`: Fetches paginated course data from AIMS
- `parse_combo_response.py`: Converts JSON responses to CSV format

See [setup/README.md](setup/README.md) for detailed instructions on:
- Finding required AIMS IDs (student degree, elective type, etc.)
- Fetching multiple pages of course data
- Converting JSON responses to CSV

**Option B: Manual CSV Creation**

Alternatively, create CSV files (`courses.csv`, `courses2.csv`, etc.) manually with these required columns:
- `rcid`: Running Course ID
- `ccode`: Course Code
- `cname`: Course Name
- `coordname`: Coordinator Name
- `ccrd`: Course Credits
- `strtdt`: Start Date (format: "DD MMM, YYYY HH:MM")
- `enddt`: End Date (format: "DD MMM, YYYY HH:MM")

See [courses_example.csv](courses_example.csv) for the expected format.

### 2. Set Authentication

Export your AIMS credentials as environment variables:

```bash
# From your browser (logged into AIMS), copy the full cookie string
export AIMS_COOKIE='JSESSIONID=...; _ga=...; ...'

# Your AIMS student ID
export AIMS_STUDENT_ID='your_student_id'

# Optional: Custom referer URL (defaults to the standard form)
export AIMS_REFERER='https://aims.iith.ac.in/aims/courseReg/studentRegForm/68'
```

**Security Note**: Never commit your actual cookies or student ID to the repository!

## Usage

### Fetch Slot Data

```bash
# Make scripts executable
chmod +x get_slots.sh get_slots.py

# Run with default settings
./get_slots.sh

# Run with custom options
./get_slots.sh --batch-size 30 --sleep-ms 200
```

### Options

- `--batch-size N`: Number of course IDs per request (default: 20)
- `--sleep-ms N`: Milliseconds to sleep between requests (default: 200)
- `--retries N`: Number of retries per batch on failure (default: 2)
- `--timeout-s N`: Request timeout in seconds (default: 30)
- `--out-csv FILE`: Output CSV file path (default: slots.csv)
- `--out-json FILE`: Output JSON file path (default: slots.json)

### Combine Course and Slot Data

After fetching slots, combine them with course information:

```bash
python3 combine_courses_slots.py
```

This creates `courses_with_slots.csv` with all course information plus slot assignments.

## Outputs

### slots.csv
One row per `(rcid, courseSlotId, courseSlotCd)` with deduplicated day/time information:
- `rcid`: Running Course ID
- `ccode`: Course Code
- `cname`: Course Name
- `courseSlotId`: Slot ID
- `courseSlotCd`: Slot Code (e.g., "A", "B", "C")
- `segName`: Segment Name
- `slotPeriodCdDays`: Pipe-separated list of slot timings

### slots.json
Structured JSON mapping with all slot information keyed by `rcid`.

### courses_with_slots.csv
Combined course and slot information for easy analysis.

## Testing

Test a single course ID fetch:

```bash
chmod +x test_single_slot.sh
./test_single_slot.sh
```

Test fetching timetable details:

```bash
chmod +x get_timetable.sh
./get_timetable.sh [course_id]
```

## Project Structure

```
.
├── setup/                     # Initial data collection scripts
│   ├── fetch_courses.sh      # Fetch course data from AIMS
│   ├── parse_combo_response.py  # Parse JSON to CSV
│   └── README.md             # Setup instructions
├── get_slots.py              # Main Python script to fetch slots
├── get_slots.sh              # Shell wrapper for get_slots.py
├── combine_courses_slots.py  # Combine courses with slot data
├── test_single_slot.sh       # Test script for single course
├── get_timetable.sh          # Test script for timetable fetch
├── courses_example.csv       # Example course data format
└── README.md                 # This file
```

## Notes

- The scripts are polite to the AIMS server with configurable delays between requests
- All sensitive data (cookies, student IDs) should be passed via environment variables
- Generated data files (*.csv, *.json) are gitignored by default
- The `old/` directory and `__pycache__/` are also gitignored

## Troubleshooting

### Authentication Errors

If you get authentication errors:
1. Ensure your AIMS session is active in your browser
2. Copy fresh cookies from browser dev tools (Network tab)
3. Make sure the JSESSIONID is not expired

### Rate Limiting

If you encounter rate limiting:
- Increase `--sleep-ms` value
- Decrease `--batch-size` value
- The script already includes automatic retries

## License

This is a utility tool for personal use with AIMS. Use responsibly and in accordance with your institution's policies.
