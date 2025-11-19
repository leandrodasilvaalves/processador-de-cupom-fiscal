#!/bin/bash

TIMESTAMP=$(date +"%d%m%y%H%M")

for FILE in *.pdf*; do
    if [ "$FILE" != "$0" ]; then
        mv "$FILE" "${TIMESTAMP}_$FILE"
        echo "Renamed: $FILE -> ${TIMESTAMP}_$FILE"
    fi
done

echo "Success. All files have been renamed: $TIMESTAMP"