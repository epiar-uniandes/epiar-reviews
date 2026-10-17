"""Check a finished OpenAlex run against what the server reported.

Reads the progress file and the CSV and reports, block by block, whether
the rows written match the number of records the server said it held, and
whether every block finished. The last check is the one that matters: the
rows counted in the file itself, because that is what the next step reads.
"""

import csv
import json
import sys

import config
import terms_line5

progress_path = (config.LOG_DIR /
                 f"{terms_line5.LINE}_openalex_progress.json")
if not progress_path.exists():
    sys.exit(f"No progress file at {progress_path}")

progress = json.loads(progress_path.read_text(encoding="utf-8"))
csv_path = config.OUTPUT_DIR / progress["csv"]

print(f"Line     {progress['line']}, {progress['source']}")
print(f"Years    {progress['year_min']} to {progress['cutoff']}")
print(f"Started  {progress['first_run']}")
print(f"File     {csv_path}\n")

problems = 0
reported = 0
written = 0
for key, block in sorted(progress["blocks"].items()):
    expected = block["expected"] or 0
    ok = block["status"] == "done" and block["written"] == expected
    if not ok:
        problems += 1
    reported += expected
    written += block["written"]
    print(f"{'ok ' if ok else '>> '} {key:42s} "
          f"{block['written']:>8,} of {expected:>8,}  {block['status']}")

print(f"\n{len(progress['blocks'])} blocks, {problems} with a problem")
print(f"{written:,} rows written, {reported:,} reported by the server")

print("\nCounting the rows in the file, this takes a moment")
rows = 0
with open(csv_path, newline="", encoding="utf-8-sig") as handle:
    for _ in csv.DictReader(handle):
        rows += 1
print(f"{rows:,} rows in the CSV")

if rows != written:
    print("\nWARNING: the file and the progress file disagree. "
          "Something was written outside the run or lost.")
elif problems:
    print("\nSome blocks did not finish or did not match. "
          "Run the download again and it will resume.")
else:
    print("\nEvery block finished and every count matches.")