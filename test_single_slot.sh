#!/bin/bash
# Test fetching slot for a single course ID
# Usage: Set AIMS_COOKIE and AIMS_STUDENT_ID environment variables, then run this script

if [ -z "${AIMS_COOKIE:-}" ]; then
  echo "Error: AIMS_COOKIE environment variable not set" >&2
  echo "Example: export AIMS_COOKIE='JSESSIONID=...; _ga=...'" >&2
  exit 1
fi

if [ -z "${AIMS_STUDENT_ID:-}" ]; then
  echo "Error: AIMS_STUDENT_ID environment variable not set" >&2
  echo "Example: export AIMS_STUDENT_ID='12345'" >&2
  exit 1
fi

curl 'https://aims.iith.ac.in/aims/courseReg/getStdntRngCrsTimeTableDtls' \
  -H 'Accept: */*' \
  -H 'Accept-Language: en-US,en;q=0.9' \
  -H 'Connection: keep-alive' \
  -H 'Content-Type: application/x-www-form-urlencoded; charset=UTF-8' \
  -b "$AIMS_COOKIE" \
  -H 'Origin: https://aims.iith.ac.in' \
  -H 'Referer: https://aims.iith.ac.in/aims/courseReg/studentRegForm/68' \
  -H 'Sec-Fetch-Dest: empty' \
  -H 'Sec-Fetch-Mode: cors' \
  -H 'Sec-Fetch-Site: same-origin' \
  -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36' \
  -H 'X-Requested-With: XMLHttpRequest' \
  -H 'sec-ch-ua: "Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "Linux"' \
  --data-raw "dataObj=%7B%22runningCourseIds%22%3A%2217174%22%2C%22studentId%22%3A%22$AIMS_STUDENT_ID%22%7D"
