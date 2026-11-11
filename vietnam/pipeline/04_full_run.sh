#!/usr/bin/env bash
# Step 4 driver (full run): while the collection shards (03b) are running, OCR/scan what has arrived (03c, incremental);
# then a final 03c pass, the person-mention step (03e). Logs in vietnam/data/full/logs/. Safe to re-run (everything is cached).
set -u
cd "$(dirname "$0")/../.."  # repo root: .venv/ and .tools/ are shared by all countries
PY=".venv/bin/python -I"
LOG=vietnam/data/full/logs
while pgrep -f "^.venv/bin/python -I vietnam/pipeline/03b_collect_docs.py full" > /dev/null; do  # anchored: a parent shell holding the same text must not match
  $PY vietnam/pipeline/03c_extract_text.py full >> $LOG/03c.log 2>&1
  sleep 60
done
$PY vietnam/pipeline/03c_extract_text.py full >> $LOG/03c.log 2>&1
$PY vietnam/pipeline/03e_people_from_text.py full >> $LOG/03e.log 2>&1
echo "FULL_RUN_DONE $(date -Is)" >> $LOG/03c.log
