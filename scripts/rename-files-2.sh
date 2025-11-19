#!/bin/bash

TIMESTAMP=$(date +"%d%m%y%H%M")
SEARCH_PATTERN="*processed_at_*.pdf"

echo "Timestamp to be used: $TIMESTAMP"
echo "---"

for ORIGINAL_FILE in $SEARCH_PATTERN; do
    if [ -f "$ORIGINAL_FILE" ]; then
        CLEAN_NAME=$(echo "$ORIGINAL_FILE" | sed 's/_processed_at_[0-9]*\.pdf/\.pdf/')
        NEW_NAME="${TIMESTAMP}_${CLEAN_NAME}"
        mv "$ORIGINAL_FILE" "$NEW_NAME"
        echo "Original: $ORIGINAL_FILE"
        echo "New:      $NEW_NAME"
        echo "---"
    fi
done

echo "Processing completed."