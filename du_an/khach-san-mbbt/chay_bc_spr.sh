#!/bin/sh
cd "$(dirname "$0")"
for he in bc spr; do
  PYTHONIOENCODING=utf-8 python ve_acad.py $he > log_$he.txt 2>&1; echo "$he mã $?"; tail -1 log_$he.txt | cut -c1-150
done
PYTHONIOENCODING=utf-8 python in_tat_ca.py > log_in.txt 2>&1; echo "in: $(grep -c True log_in.txt) tờ"
