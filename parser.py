import pdfplumber
import re

# --- Known operations that get columns in the master sheet --------------
KNOWN_OPERATIONS = {'PROWATERJE', 'CNCMILL', 'CNCMILLPRO', 'CNCLATHE', 'CNCLATHEPR'}

# Maps variant names to their master column name
OPERATION_MAP = {
    'PROWATERJE': 'PROWATERJE',
    'CNCMILL': 'CNCMILL',
    'CNCMILLPRO': 'CNCMILL',
    'CNCLATHE': 'CNCLATHE',
    'CNCLATHEPR': 'CNCLATHE',
    'CNCLATHELG': 'CNCLATHE',
}

# --- Regex --------------------------------------------------------------
# Matches lines like:
# 30 CNCMILL Setup 1.00 H Cycle 4.00 M Total 4.33 H Qty 50 End Date: 05/28/26
# 40 QC Setup .00 M Cycle .00 M Total .00 H Qty 50 End Date: 05/29/2026
operation_pattern = re.compile(
    r"\d+\s+([A-Z]+)\s+Setup\s*([\d.]+)\s*[HM].*?Total\s+([\d.]+)\s+[HM].*?End Date:\s+(\d{2}/\d{2}/\d{4})"
)

# Matches the follow number at the top of each WO page e.g. 75560-01
follow_pattern = re.compile(r"\b(\d{5}-\d{2})\b")


def extract_val(text, label):
    """Pull the value that sits directly after a label on the same line."""
    if label in text:
        parts = text.split(label)
        if len(parts) > 1:
            return parts[1].split('\n')[0].strip()
    return "N/A"



def parse_page(page_text, page_number):
    """
    Parse a single WO page and return a result dict containing:
    - header fields(WO number, customer, finish date)
    - known operations list
    - flagged operations list
    """
    result = {
        'page_number': page_number,
        'WO_Number': '',
        'Customer': '',
        'Finish_Date': '',
        'Description': '',
        'known_ops': [],      # list of dicts for PROWATERJE, CNCMILL, LATHE
        'flagged_ops': [],    # list of dicts for anything else
    }

    # ---Header Fields -----------------------------------------------
    result['WO_Number'] = extract_val(page_text, "Job Number:")
    result['Customer'] = extract_val(page_text, "Customer:")
    result['Finish_Date'] = extract_val(page_text, "Finish Date:")
    description = extract_val(page_text, "Description:")
    quantity = extract_val(page_text, "Quantity:")
    result['Description'] = f"{description} ({quantity})"

    # Fallback: try to find follow number directly if Job Number label is missing
    if result['WO_Number'] == 'N/A':
        match = follow_pattern.search(page_text)
        if match:
            result['WO_Number'] = match.group(1)

    # --- Operation Lines --------------------------------------------
    for line in page_text.split('\n'):
        match = operation_pattern.search(line)
        if match:
            op_name = match.group(1)
            op_time = float(match.group(3))
            op_end_date = match.group(4)

            op_dict = {
                'Operation': op_name,
                'Time': op_time,
                'End_Date': op_end_date
            }

            if op_name in KNOWN_OPERATIONS:
                result['known_ops'].append({
                    'Operation': OPERATION_MAP[op_name], # normalized name
                    'Time': op_time,
                    'End_Date': op_end_date
                })
            else:
                result['flagged_ops'].append({
                    'Operation': op_name, # raw name so you know exactly what was in the PDF
                    'Time': op_time,
                    'End_Date': op_end_date
                })
    return result


def parse_pdf(pdf_path):
    """
    Open the pdf, parse every page, return two lists:
    - parsed_pages : one result dict per WO page
    - parse_errors : any pages that failed with an error message
    """
    parsed_pages = []
    parse_errors = []

    print(f"Opening {pdf_path}...")

    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            print(f"Found {total_pages} page(s) to process.")

            current_wo = None # track the last seen WO header

            for i, page in enumerate(pdf.pages):
                page_number = i + 1
                try:
                    text = page.extract_text()

                    if not text or text.strip() == "":
                        parse_errors.append({
                            'page_number': page_number,
                            'error': 'Page returned no text - may be a scanned image'
                        })
                        continue

                    # ── WO header page ────────────────────────────────────
                    if "Job Number:" in text and "Customer:" in text:
                        current_wo = parse_page(text, page_number)
                        parsed_pages.append(current_wo)
                        print(f"  Page {page_number}: {current_wo['WO_Number']} - {current_wo['Customer']}") 
                        
                    # ── Every other page --- scan for operations ───────────────────
                    elif current_wo is not None:
                        print(f"  Page {page_number}: scanning for operations ({current_wo['WO_Number']})")

                        # Parse operations from this page and add to surrent WO
                        for line in text.split('\n'): 
                            match = operation_pattern.search(line)
                            if match:
                                op_name = match.group(1)
                                op_time = float(match.group(3))
                                op_end_date = match.group(4)

                                if op_name in KNOWN_OPERATIONS:
                                    current_wo['known_ops'].append({
                                        'Operation': OPERATION_MAP[op_name], # normalized name
                                        'Time': op_time,
                                        'End_Date': op_end_date
                                    })
                                else:
                                    current_wo['flagged_ops'].append({
                                        'Operation': op_name, # raw name so you know exactly what was in the PDF
                                        'Time': op_time,
                                        'End_Date': op_end_date
                                    })

                    else:
                        print(f"  Page {page_number}: skipped - no WO context yet")

                except Exception as e:
                    parse_errors.append({
                        'page_number': page_number,
                        'error': str(e)
                    })
                    print(f"  Page {page_number}: ERROR - {e}")

    except Exception as e:
        print(f"Failed to open PDF: {e}")

    return parsed_pages, parse_errors
            