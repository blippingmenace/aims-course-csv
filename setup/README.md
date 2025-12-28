# Initial Setup Scripts

This directory contains scripts for the **initial data collection** from AIMS to create the course CSV files.

## Overview

The workflow has two steps:
1. Fetch course data from AIMS (JSON response)
2. Parse the JSON response to CSV format

## Prerequisites

You need to obtain several IDs from your AIMS session. These can be found by:
1. Logging into AIMS
2. Opening the course registration page
3. Opening browser Developer Tools (F12) → Network tab
4. Looking for `comboHelpAjax` requests when the page loads
5. Examining the request payload

## Required Environment Variables

```bash
# Basic authentication (same as main scripts)
export AIMS_COOKIE='your_session_cookie'
export AIMS_STUDENT_ID='your_student_id'

# Additional IDs (find these in browser dev tools)
export AIMS_STUDENT_DEGREE_ID='13863'    # Your degree program ID
export AIMS_ELECTIVE_TYPE_ID='22'        # Elective type ID
export AIMS_ACAD_PERIOD_ID='68'          # Current academic period ID
export AIMS_REG_TYPE_ID='1'              # Registration type ID
```

## Usage

### Step 1: Fetch Course Data

The AIMS system paginates results. You may need to fetch multiple pages:

```bash
# Make the script executable
chmod +x fetch_courses.sh

# Fetch page 1 (first 200 courses)
./fetch_courses.sh 1 courses_page1.json

# Fetch page 2 if there are more courses
./fetch_courses.sh 2 courses_page2.json

# And so on...
./fetch_courses.sh 3 courses_page3.json
```

The response JSON will show `comboTotalRecordCount` to tell you how many total courses exist.

### Step 2: Convert JSON to CSV

```bash
# Parse each JSON file to CSV
python3 parse_combo_response.py courses_page1.json courses.csv
python3 parse_combo_response.py courses_page2.json courses2.csv
python3 parse_combo_response.py courses_page3.json courses3.csv
```

### Step 3: Move to Main Directory

```bash
# Move the CSV files to the main directory
mv courses*.csv ../
```

## Output Format

The generated CSV files will contain these columns:
- `rcId`: Running Course ID (used as `rcid` in main scripts)
- `cCode`: Course Code
- `cName`: Course Name
- `coordName`: Coordinator Name
- `cCrd`: Course Credits
- `strtDt`: Course Start Date
- `endDt`: Course End Date
- And many more fields...

## Finding Your IDs

### Method 1: Browser Developer Tools
1. Log into AIMS
2. Open browser Dev Tools (F12)
3. Go to Network tab
4. Navigate to course registration page
5. Look for `comboHelpAjax` request
6. View the request payload to find your IDs

### Method 2: Page Source
1. Right-click on the course registration page
2. "View Page Source"
3. Search for terms like `studentDegreeId`, `electiveTypeId`, etc.

## Notes

- The scripts use the same authentication as the main slot fetcher
- The query string in `fetch_courses.sh` is very long - this is normal for AIMS
- Page size is set to 200 by default (adjust if needed)
- The data fetched here becomes the input for the main slot fetching scripts
- These scripts only need to be run once at the beginning of a semester or when course listings change

## Troubleshooting

**Q: Getting authentication errors?**
A: Make sure your AIMS_COOKIE is fresh and valid. Cookies expire after a period of inactivity.

**Q: Not getting any results?**
A: Check that your AIMS_ACAD_PERIOD_ID matches the current semester/period in AIMS.

**Q: IDs don't match?**
A: These IDs are institution and semester-specific. You must extract them from your own AIMS session.
