import pdfplumber
import csv
import os
import re

pdf_path = "AMS WO#75579.pdf"
csv_file = "work_order_data.csv"

row_pattern = re.compile(r"(PROWATERJE|CNCMILL|CNCLATHE|).*?Total\s+([\d.]+)\s+[HM].*?End Date:\s+(\d{2}/\d{2}/\d{4})")

final_rows = []

def extract_machine_data(text):
    results = []
    lines = text.split('\n')

    for line in lines:
        match = row_pattern.search(line)
        if match:
            results.append({
                'Machine': match.group(1),
                'Total_Time': match.group(2),
                'End_Date': match.group(3)
            })
    return results

def extract_val(text, label):
    if label in text:
        parts = text.split(label)
        if len(parts) > 1:
            return parts[1].split('\n')[0].strip()
    return "N/A"

# 1. Extract Data
print(f"Opening {pdf_path}...")
try:
    with pdfplumber.open(pdf_path) as pdf:
        text = pdf.pages[0].extract_text()

        wo_num = extract_val(text, "Job Number:")
        finish_date = extract_val(text, "Finish Date:")
        customer = extract_val(text, "Customer:")

        detected_machines = extract_machine_data(text)

        # Build one wide row per WO with machines as columns
        combined_row = {
            'WO_Number': wo_num,
            'Customer': customer,
            'Total': 0.0,
            'End_Date': 'N/A',
            'Total': 0.0,
            'End_Date': 'N/A',
            'Total': 0.0,
            'End_Date': 'N/A',
            'Finish_Date': finish_date
        }

        for machine_info in detected_machines:
            machine = machine_info['Machine']
            time = float(machine_info['Total_Time'])
            end_date = machine_info['End_Date']

            if machine == 'PROWATERJE':
                combined_row['Total'] = time
                combined_row['End_Date'] = end_date
            elif machine == 'CNCLATHE':
                combined_row['Total'] = time
                combined_row['End_Date'] = end_date
            elif machine == 'CNCMILL':
                combined_row['Total'] = time
                combined_row['End_Date'] = end_date
        final_rows.append(combined_row)
        print(f"Data successfully extracted! Found {len(detected_machines)} machine operations.")

except Exception as e:
    print(f"Error reading PDF: {e}")

# 2. Save to CSV
if final_rows:
    headers = ['WO_Number', 'Customer', 'Total', 'End_Date', 'Total', 'End_Date', 'Total', 'End_Date', 'Finish_Date']
    file_is_new = not os.path.isfile(csv_file)

    with open(csv_file, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        if file_is_new:
            writer.writeheader()
        writer.writerows(final_rows)

    print(f"Machine data appended to {csv_file}")
else:
    print("No data was written because no machine rows were found.")