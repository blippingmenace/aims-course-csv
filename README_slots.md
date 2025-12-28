## Fetch slots for all courses

This repo already has `courses*.csv` with the `rcid` column (AIMS `runningCourseId`).

### 1) Set your auth cookie + student id

From your browser (logged into AIMS), copy the full request cookie string.

```bash
export AIMS_COOKIE='JSESSIONID=...; _ga=...; ...'
export AIMS_STUDENT_ID='your_student_id'
```

### 2) Run

```bash
chmod +x get_slots.sh get_slots.py
./get_slots.sh
```

Optional tuning:

```bash
./get_slots.sh --batch-size 30 --sleep-ms 200
```

### Outputs

- `slots.csv`: one row per `(rcid, courseSlotId, courseSlotCd)` with deduped `slotPeriodCdDays`
- `slots.json`: structured mapping keyed by `rcid`
