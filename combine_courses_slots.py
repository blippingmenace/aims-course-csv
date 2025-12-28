#!/usr/bin/env python3
"""Create courses_with_slots.csv by analyzing dates from courses*.csv to determine segments."""

import csv
import json
from pathlib import Path
from datetime import datetime

def parse_date(date_str):
    """Parse date string like '05 Jan, 2026 00:00'"""
    try:
        return datetime.strptime(date_str.strip(), '%d %b, %Y %H:%M')
    except:
        return None

def determine_segment(start_dt, end_dt):
    """
    Determine segment based on start and end dates.
    Segments (approximately):
    1: Jan 05 - Feb 09
    2: Feb 10 - Mar 09
    3: Mar 10 - Apr 09  (but data shows up to Mar 20)
    4: Mar 23 - Apr 27
    5-6: Later segments
    
    Common patterns:
    - 1-6: Jan 05 -> Apr 27 (full semester)
    - 1-4: Jan 05 -> Mar 20/23
    - 1-3: Jan 05 -> Feb end
    - 4-6: Mar -> Apr 27
    - 1-2: Jan 05 -> Feb 09
    - 2-4: Feb 10 -> Mar 20
    """
    if not start_dt or not end_dt:
        return ''
    
    # Define approximate segment boundaries
    jan_05 = datetime(2026, 1, 5)
    feb_09 = datetime(2026, 2, 9)
    feb_10 = datetime(2026, 2, 10)
    feb_26 = datetime(2026, 2, 26)
    mar_09 = datetime(2026, 3, 9)
    mar_20 = datetime(2026, 3, 20)
    mar_23 = datetime(2026, 3, 23)
    apr_27 = datetime(2026, 4, 27)
    
    start_seg = None
    end_seg = None
    
    # Determine start segment
    if start_dt <= jan_05:
        start_seg = 1
    elif start_dt <= feb_10:
        start_seg = 2
    elif start_dt <= feb_26:
        start_seg = 3
    elif start_dt <= mar_23:
        start_seg = 4
    else:
        start_seg = 5
    
    # Determine end segment
    if end_dt <= feb_09:
        end_seg = 2
    elif end_dt <= mar_09:
        end_seg = 3
    elif end_dt <= mar_20:
        end_seg = 4
    elif end_dt <= apr_27:
        end_seg = 6
    else:
        end_seg = 6
    
    if start_seg and end_seg:
        return f"{start_seg}-{end_seg}"
    return ''

# Read all courses from courses*.csv
courses = {}
for csv_file in ['courses.csv', 'courses2.csv', 'courses3.csv']:
    if not Path(csv_file).exists():
        continue
    
    with open(csv_file, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rcid = (row.get('rcid') or '').strip()
            if not rcid:
                continue
            
            # Keep first occurrence of each course
            if rcid not in courses:
                strtdt = (row.get('strtdt') or '').strip()
                enddt = (row.get('enddt') or '').strip()
                
                start_dt = parse_date(strtdt)
                end_dt = parse_date(enddt)
                segment = determine_segment(start_dt, end_dt)
                
                courses[rcid] = {
                    'rcid': rcid,
                    'ccode': (row.get('ccode') or '').strip(),
                    'cname': (row.get('cname') or '').strip(),
                    'coordname': (row.get('coordname') or '').strip(),
                    'ccrd': (row.get('ccrd') or '').strip(),
                    'segment': segment,
                    'slots': ''
                }

# Read slots and segments from slots.json (more accurate than date calculation)
slots_map = {}
segment_map = {}
if Path('slots.json').exists():
    with open('slots.json') as f:
        data = json.load(f)
        for rcid, course in data.items():
            for slot in course.get('slots', []):
                slot_cd = slot.get('courseSlotCd', '').strip()
                seg_name = slot.get('segName', '').strip()
                if slot_cd:
                    slots_map[rcid] = slot_cd
                if seg_name:
                    segment_map[rcid] = seg_name

# Fallback: read from slots.csv if json doesn't exist
if not slots_map and Path('slots.csv').exists():
    with open('slots.csv', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Find the actual column names (may have spaces)
            rcid_key = next((k for k in row.keys() if 'rcid' in k.lower()), 'rcid')
            slot_key = next((k for k in row.keys() if 'courseSlotCd' in k), 'courseSlotCd')
            seg_key = next((k for k in row.keys() if 'segName' in k), 'segName')
            
            rcid = (row.get(rcid_key) or '').strip()
            slot = (row.get(slot_key) or '').strip()
            segment = (row.get(seg_key) or '').strip()
            if rcid:
                if slot:
                    slots_map[rcid] = slot
                if segment:
                    segment_map[rcid] = segment

# Merge slots and segments into courses
for rcid, course in courses.items():
    if rcid in slots_map:
        course['slots'] = slots_map[rcid]
    # Use API segment if available, otherwise use computed segment
    if rcid in segment_map:
        course['segment'] = segment_map[rcid]

# Write output
with open('courses_with_slots.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['ccode', 'cname', 'coordname', 'ccrd', 'segment', 'slots'])
    writer.writeheader()
    
    # Sort by course code
    sorted_courses = sorted(courses.values(), key=lambda x: x['ccode'])
    for course in sorted_courses:
        writer.writerow({
            'ccode': course['ccode'],
            'cname': course['cname'],
            'coordname': course['coordname'],
            'ccrd': course['ccrd'],
            'segment': course['segment'],
            'slots': course['slots']
        })

print(f"Created courses_with_slots.csv with {len(courses)} courses")
print(f"  - {len([c for c in courses.values() if c['slots']])} courses with slots")
print(f"  - {len([c for c in courses.values() if c['segment']])} courses with segments")
