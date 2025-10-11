from datetime import datetime
import hash_calculator
import create_tables
import os

start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
print(f"[{start}] - Starting processing...")

pending_dir = "./pdf-files/pending"
pending_files = os.listdir(pending_dir)
print(f"Found {len(pending_files)} files in {pending_dir}.")
for file in pending_files:
    print(f"Processing file: {file}")
    file_path = os.path.join(pending_dir, file)
    file_hash = hash_calculator.calculate(file_path)
    print(f"Calculated hash for {file}: {file_hash}")