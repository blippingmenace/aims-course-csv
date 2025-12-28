#!/usr/bin/env bash
set -euo pipefail

# Set these environment variables before running:
# export AIMS_COOKIE='your_cookie_here'
# export AIMS_STUDENT_ID='your_student_id'
# export AIMS_REFERER='https://aims.iith.ac.in/aims/courseReg/studentRegForm/YOUR_ID'

if [ -z "${AIMS_COOKIE:-}" ]; then
  echo "Error: AIMS_COOKIE environment variable not set" >&2
  exit 1
fi

if [ -z "${AIMS_STUDENT_ID:-}" ]; then
  echo "Error: AIMS_STUDENT_ID environment variable not set" >&2
  exit 1
fi

REFERER="${AIMS_REFERER:-https://aims.iith.ac.in/aims/courseReg/studentRegForm/68}"

exec ./get_slots.py \
  --student-id "$AIMS_STUDENT_ID" \
  --cookie "$AIMS_COOKIE" \
  --referer "$REFERER" \
  "$@"
