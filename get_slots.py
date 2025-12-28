#!/usr/bin/env python3
"""Fetch and dedupe slot timings for all running courses (rcid) from AIMS.

This script calls:
  https://aims.iith.ac.in/aims/courseReg/getStdntRngCrsTimeTableDtls

It expects an authenticated session cookie (copy from your browser).

Outputs:
- slots.csv  (one row per course-slot, with deduped day/time list)
- slots.json (structured mapping)
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


AIMS_TIMETABLE_URL = "https://aims.iith.ac.in/aims/courseReg/getStdntRngCrsTimeTableDtls"
DEFAULT_REFERER = "https://aims.iith.ac.in/aims/courseReg/studentRegForm/68"


@dataclass(frozen=True)
class CourseMeta:
    rcid: str
    ccode: str
    cname: str


def eprint(*args: object) -> None:
    print(*args, file=sys.stderr)


def read_courses(csv_paths: list[Path]) -> dict[str, CourseMeta]:
    courses: dict[str, CourseMeta] = {}

    for csv_path in csv_paths:
        if not csv_path.exists():
            continue

        with csv_path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                continue

            # Your CSV uses rcid/ccode/cname.
            for row in reader:
                rcid = (row.get("rcid") or "").strip()
                if not rcid:
                    continue

                # Keep first seen meta for a given rcid.
                if rcid in courses:
                    continue

                ccode = (row.get("ccode") or "").strip()
                cname = (row.get("cname") or "").strip()
                courses[rcid] = CourseMeta(rcid=rcid, ccode=ccode, cname=cname)

    return courses


def chunked(values: list[str], n: int) -> Iterable[list[str]]:
    if n <= 0:
        raise ValueError("batch size must be > 0")
    for i in range(0, len(values), n):
        yield values[i : i + n]


def post_timetable(
    *,
    running_course_ids: list[str],
    student_id: str,
    cookie: str,
    referer: str,
    user_agent: str,
    timeout_s: int,
) -> list[dict]:
    payload_obj = {"runningCourseIds": ",".join(running_course_ids), "studentId": str(student_id)}

    # Server expects form data with a JSON-ish string in dataObj.
    data = urllib.parse.urlencode(
        {"dataObj": json.dumps(payload_obj, separators=(",", ":"))}
    ).encode("utf-8")

    req = urllib.request.Request(AIMS_TIMETABLE_URL, data=data, method="POST")
    req.add_header("Accept", "*/*")
    req.add_header("Content-Type", "application/x-www-form-urlencoded; charset=UTF-8")
    req.add_header("X-Requested-With", "XMLHttpRequest")
    req.add_header("Origin", "https://aims.iith.ac.in")
    if referer:
        req.add_header("Referer", referer)
    if user_agent:
        req.add_header("User-Agent", user_agent)
    if cookie:
        req.add_header("Cookie", cookie)

    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        raw = resp.read().decode("utf-8", errors="replace")

    # This endpoint returns a JSON array.
    parsed = json.loads(raw)
    if not isinstance(parsed, list):
        raise ValueError(f"Unexpected response type: {type(parsed)}")
    return parsed


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch deduped timetable slots for all courses")
    parser.add_argument(
        "--csv",
        dest="csv_paths",
        action="append",
        default=[],
        help="Course CSV file (can repeat). Defaults to courses*.csv in cwd.",
    )
    parser.add_argument(
        "--student-id",
        default="",
        help="Your AIMS studentId (required - pass via CLI or env var AIMS_STUDENT_ID).",
    )
    parser.add_argument(
        "--cookie",
        default="",
        help="Cookie header value (required - pass via CLI or env var AIMS_COOKIE).",
    )
    parser.add_argument(
        "--referer",
        default=DEFAULT_REFERER,
        help=f"Referer header (default: {DEFAULT_REFERER}).",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=20,
        help="How many rcids per request (default: 20).",
    )
    parser.add_argument(
        "--sleep-ms",
        type=int,
        default=200,
        help="Sleep between requests to be polite (default: 200ms).",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=2,
        help="Retries per batch on network/HTTP errors (default: 2).",
    )
    parser.add_argument(
        "--timeout-s",
        type=int,
        default=30,
        help="Request timeout seconds (default: 30).",
    )
    parser.add_argument(
        "--out-csv",
        default="slots.csv",
        help="Output CSV path (default: slots.csv).",
    )
    parser.add_argument(
        "--out-json",
        default="slots.json",
        help="Output JSON path (default: slots.json).",
    )

    args = parser.parse_args()

    # Get credentials from args or environment
    student_id = args.student_id or os.environ.get("AIMS_STUDENT_ID", "")
    cookie = args.cookie or os.environ.get("AIMS_COOKIE", "")

    if not student_id:
        eprint("ERROR: missing student id. Pass --student-id or set AIMS_STUDENT_ID env var")
        return 2
    if not cookie:
        eprint("ERROR: missing cookie. Pass --cookie or set AIMS_COOKIE env var")
        return 2

    # Determine CSV inputs.
    csv_paths: list[Path]
    if args.csv_paths:
        csv_paths = [Path(p) for p in args.csv_paths]
    else:
        csv_paths = sorted(Path.cwd().glob("courses*.csv"))

    courses = read_courses(csv_paths)
    rcids = sorted(courses.keys(), key=lambda x: int(x) if x.isdigit() else x)
    if not rcids:
        eprint("ERROR: no rcid found in provided CSVs")
        return 2

    # Collect (rcid, slotId, slotCd) -> set(day-time), also track segName
    slot_map: dict[tuple[str, str, str], set[str]] = defaultdict(set)
    segment_map: dict[tuple[str, str, str], str] = {}

    user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"

    total_batches = (len(rcids) + args.batch_size - 1) // args.batch_size
    for batch_index, batch in enumerate(chunked(rcids, args.batch_size), start=1):
        attempt = 0
        while True:
            attempt += 1
            try:
                items = post_timetable(
                    running_course_ids=batch,
                    student_id=student_id,
                    cookie=cookie,
                    referer=args.referer,
                    user_agent=user_agent,
                    timeout_s=args.timeout_s,
                )

                for it in items:
                    rcid = str(it.get("runningCourseId", "") or "").strip()
                    slot_id = str(it.get("courseSlotId", "") or "").strip()
                    slot_cd = str(it.get("courseSlotCd", "") or "").strip()
                    day_time = str(it.get("slotPeriodCdDays", "") or "").strip()
                    seg_name = str(it.get("segName", "") or "").strip()

                    if not rcid or not day_time:
                        continue

                    key = (rcid, slot_id, slot_cd)
                    slot_map[key].add(day_time)
                    if seg_name and key not in segment_map:
                        segment_map[key] = seg_name

                print(f"[{batch_index}/{total_batches}] fetched {len(batch)} courses -> {len(items)} rows")
                break

            except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError) as ex:
                if attempt <= args.retries + 1:
                    eprint(f"WARN: batch {batch_index}/{total_batches} attempt {attempt} failed: {ex}")
                    time.sleep(0.8)
                    continue
                eprint(f"ERROR: batch {batch_index}/{total_batches} failed after retries: {ex}")
                break

        time.sleep(max(0, args.sleep_ms) / 1000.0)

    # Build JSON output.
    out_json: dict[str, dict] = {}
    for (rcid, slot_id, slot_cd), day_times in slot_map.items():
        course = courses.get(rcid, CourseMeta(rcid=rcid, ccode="", cname=""))
        seg_name = segment_map.get((rcid, slot_id, slot_cd), "")
        out_json.setdefault(
            rcid,
            {"rcid": rcid, "ccode": course.ccode, "cname": course.cname, "slots": []},
        )
        out_json[rcid]["slots"].append(
            {
                "courseSlotId": slot_id,
                "courseSlotCd": slot_cd,
                "segName": seg_name,
                "slotPeriodCdDays": sorted(day_times),
            }
        )

    # Stable ordering.
    for rcid in out_json:
        out_json[rcid]["slots"].sort(key=lambda s: (s.get("courseSlotId", ""), s.get("courseSlotCd", "")))

    Path(args.out_json).write_text(json.dumps(out_json, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # CSV output: one row per courseSlot (deduped day-times joined).
    with Path(args.out_csv).open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "rcid",
                "ccode",
                "cname",
                "cegName",
                "slotPeriodCdDays",
            ],
        )
        writer.writeheader()
        for (rcid, slot_id, slot_cd) in sorted(
            slot_map.keys(), key=lambda k: (int(k[0]) if k[0].isdigit() else k[0], k[1], k[2])
        ):
            course = courses.get(rcid, CourseMeta(rcid=rcid, ccode="", cname=""))
            day_times = sorted(slot_map[(rcid, slot_id, slot_cd)])
            seg_name = segment_map.get((rcid, slot_id, slot_cd), "")
            writer.writerow(
                {
                    "rcid": rcid,
                    "ccode": course.ccode,
                    "cname": course.cname,
                    "courseSlotId": slot_id,
                    "courseSlotCd": slot_cd,
                    "segName": seg_name,
                    "slotPeriodCdDays": " | ".join(day_times),
                }
            )

    print(f"Wrote {args.out_csv} and {args.out_json}")
    return 0


if __name__ == "__main__":
    import os

    raise SystemExit(main())
