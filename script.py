import pdfplumber
import csv
import os

# 1. Extract data from PDF
pdf_path = "AMS WO#75680.pdf"  # Make sure pdf is in same folder as script
csv_file = "work_order_data.csv"

def extract_val(text, label):
    if label in text:
        parts = text.split(label)
        if len(parts) > 1:
            return parts[1].split('\n')[0].strip()
    return "N/A"

# 2. Extract Data
print(f"Opening {pdf_path}...")
try:
    with pdfplumber.open(pdf_path) as pdf:
        text = pdf.pages[0].extract_text()

        data = {
            'WO_Number': extract_val(text, "Job Number:"),
            'Finish Date': extract_val(text, "Finish Date:"),
            'Customer': extract_val(text, "Customer:")
        }
        print("Data successfully extracted!")
except Exception as e:
    print(f"Error reading PDF: {e}")
    data = None

# 3. Save to CSV
if data:
    headers = ['WO_Number', 'Finish Date', 'Customer']
    file_is_new = not os.path.isfile(csv_file)

    with open(csv_file, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        if file_is_new:
            writer.writeheader()
        writer.writerow(data)

    print(f"Result append to {csv_file}")