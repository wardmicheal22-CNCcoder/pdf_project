import pdfplumber
import csv
import os
import re

pdf_path = "AMS WO#75680.pdf"
csv_file = "work_order_data.csv"

# Regex pattern explanation:
# (CNCMILL|QC|CNC[A-Z]*) -> Captures the machine name
# .*?Total\s+([\d.]+)\s+[HM] -> Finds "Total", grabs the number, ignores H or M
# .*?End Date:\s+(\d{2}/\d{2}/\d{4}) -> Finds "End Date:", grabs the MM/DD/YYYY date
row_pattern = re.compile(r"(CNCMILL|QC)\s*.*?Total\s+([\d.]+)\s+[HM].*?End Date:\s+(\d{2}/\d{2}/\d{4})")

final_rows = []

def extract_machine_data(text):
    results = []
    lines = text.split('\n')

    for line in lines:
        match = row_pattern.search(line)
        if match:
            machine_name = match.group(1)
            total_time = match.group(2)
            end_date = match.group(3)

            results.append({
                'Machine': machine_name,
                'Total_Time': total_time,
                'End_Date': end_date
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

        for machine_info in detected_machines:
            combined_row = {
                'WO_Number': wo_num,
                'Finish Date': finish_date,
                'Customer': customer,
                'Machine': machine_info['Machine'],
                'Total_Time': float(machine_info['Total_Time']),
                'End_Date': machine_info['End_Date'],
            }
            final_rows.append(combined_row)

        print(f"Data successfully extracted! Found {len(final_rows)} machine operations.")

except Exception as e:
        print(f"Error reading PDF: {e}")

# 2. Save to a seperate CSV for machine tracking
if final_rows:
    headers = ['WO_Number', 'Finish Date', 'Customer', 'Machine', 'Total_Time', 'End_Date']
    file_is_new = not os.path.isfile(csv_file)

    with open(csv_file, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        if file_is_new:
            writer.writeheader()

        for row in final_rows:
            writer.writerow(row)

    print(f"Machine data appended to {csv_file}")
else:
    print("No data was written because no machine rows were found.")
            

    
