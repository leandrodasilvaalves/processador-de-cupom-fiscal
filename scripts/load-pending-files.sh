#!/bin/bash

echo cleaning pending files
rm pdf-files/pending/*.pdf

echo cleaning processed files
rm pdf-files/processed/*.pdf

echo loading sample files to pending folder
cp pdf-files/0-samples/*.pdf pdf-files/pending/