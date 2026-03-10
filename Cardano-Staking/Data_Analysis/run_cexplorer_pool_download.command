#!/bin/zsh
set -u

cd "/Users/juancho"
export CEXPLORER_API_KEY="0-0010-e96ee948-b131-40a1-b754-1cb56fb73fa5-3ec78b6accad5ab610edc"

LOG_FILE="/Users/juancho/cexplorer_pool_download.log"
CSV_FILE="/Users/juancho/staking_pools.csv"

echo "Starting download..." > "$LOG_FILE"
echo "Time: $(date)" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

python3 "/Users/juancho/download_cexplorer_pools_to_csv.py" --output "$CSV_FILE" --limit 100 >> "$LOG_FILE" 2>&1
EXIT_CODE=$?

echo "" >> "$LOG_FILE"
echo "Exit code: $EXIT_CODE" >> "$LOG_FILE"

echo ""
if [ "$EXIT_CODE" -eq 0 ]; then
  echo "Done."
  echo "CSV file: $CSV_FILE"
else
  echo "Download failed."
  echo "Check log file: $LOG_FILE"
fi
echo ""
echo "Press Enter to close."
read
