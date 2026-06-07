import re

operation_pattern = re.compile(
    r"\d+\s+([A-Z]+)\s+Setup\s*([\d.]+)\s*[HM].*?Total\s+([\d.]+)\s+[HM].*?End Date:\s+(\d{2}/\d{2}/\d{4})"
)

# Paste exact lines from the raw text output
test_lines = [
        "30 PROWATERJE Setup15.00 M Cycle11.50 M Total 1.78 H Qty 8 End Date: 04/28/2026",
        "40 CNCMILL Setup 1.50 H Cycle 1.00 H Total 9.50 H Qty 8 End Date: 05/29/2026",
        "20 CNCLATHEPR Setup30.00 M Cycle 3.00 M Total 1.30 H Qty 16 End Date: 05/29/2026",
        "30 CNCMILLPRO Setup 1.00 H Cycle 3.00 M Total 1.80 H Qty 16 End Date: 05/29/2026",
        "20 SAW PR Setup15.00 M Cycle 45.00 S Total .45 H Qty 16 End Date: 04/28/2026",
]

for line in test_lines:
    match = operation_pattern.search(line)
    if match:
        print(f"MATCH: {match.groups()}")
    else:
        print(f"NO MATCH: {line}")
        