from parser import parse_pdf
from normalizer import normalize_all

parsed, errors = parse_pdf("AMS WO#75278.pdf")
master_rows, flagged_rows = normalize_all(parsed)

print("\n── Master Rows ──")
for row in master_rows:
    print(row)

print("\n── Flagged Rows ──")
for row in flagged_rows:
    print(row)

"""
1Nu8ynRnYhwRKBX44FP1CG5domsL-0SEA-OoH2AsSirg
"""
