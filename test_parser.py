from parser import parse_pdf
from normalizer import normalize_all
from sheets_writer import write_to_sheets

parsed, errors = parse_pdf("AMS WO#75278.pdf")
master_rows, flagged_rows = normalize_all(parsed)
write_to_sheets(master_rows, flagged_rows)
"""
1Nu8ynRnYhwRKBX44FP1CG5domsL-0SEA-OoH2AsSirg
"""
