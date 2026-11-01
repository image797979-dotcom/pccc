#!/bin/sh
# Vẽ lần lượt 4 hệ PCCC; mỗi hệ một log.
cd "$(dirname "$0")"
for he in bc spr hong cs; do
  echo "== BẮT ĐẦU $he"
  PYTHONIOENCODING=utf-8 python ve_acad.py $he > log_$he.txt 2>&1
  echo "== KẾT THÚC $he mã $?"
  tail -3 log_$he.txt
done
