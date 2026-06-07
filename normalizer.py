# normalizer.py

# This maps the operation names coming out of parser.py
# to the column names we want in Excel.
# Parser gives us 'PROWATERJE', 'CNCMILL', 'CNCLATHE'
# Excel eants 'WJ, 'Mill', 'Lathe'
COLUMN_MAP = {
    'PROWATERJE': 'WJ',
    'CNCLATHE':   'Lathe',
    'CNCMILL':    'Mill',
}

def normalize(parsed_page):
    """
    Takes one parsed page dict from parser.py and returns
    one flat row dict ready to write to Excel.
    """

    # Step 1 - Start with a blank row using your exact Excel column order.
    # Every machine gets two columns: End_Date and Time.
    # We default everything to 'N/A' so that WOs with no
    # lathe operation still produce a clean row instead of an error.
    row = {
        'Customer':      parsed_page['Customer'],
        'WO_Number':     parsed_page['WO_Number'],
        'Description':   parsed_page['Description'],
        'WJ_End_Date':   'N/A',
        'WJ_Time':       'N/A',
        'Lathe_End_Date':'N/A',
        'Lathe_Time':    'N/A',
        'Mill_End_Date': 'N/A',
        'Mill_Time':     'N/A',
        'Finish_Date':   parsed_page['Finish_Date'],
    }

    # Step 2 - Loop through the known operations the parser found
    # and fill in the correct columns using COLUMN_MAP.
    # For example if op['Operation'] is 'CNCMILL' and 'Mill_End_Date'.
    # gives us 'Mill', so we write to 'Mill_Time' and 'Mill_End_Date'.
    for op in parsed_page['known_ops']:
        col = COLUMN_MAP.get(op['Operation'])

        if col: # only write if the operation is in our map
            row[f'{col}_End_Date'] = op['End_Date']
            row[f'{col}_Time']     = op['Time']

    # Step 3 - Return the completed row.
    # Flagged ops are not written here - they go to
    # the Flagged_Operations sheet in excel_writer.py
    return row

def normalize_all(parsed_pages):
    """
    Runs normalize() on every parsed page and returns
    a list of rows ready for Excel.
    Also passes flagged ops through so excel_writer.py
    can write them to the Flagged_Operations sheet.
    """
    master_rows = []
    flagged_rows = []

    for page in parsed_pages:
        # Build the master row for this WO
        master_rows.append(normalize(page))

        # Collect any flagged operations, adding WO context
        # so the Flagged sheet tells you exactly which WO they came from
        for op in page['flagged_ops']:
            flagged_rows.append({
                'WO_Number':       page['WO_Number'],
                'Customer':        page['Customer'],
                'Operation_Found': op['Operation'],
                'End_Date':        op['End_Date'],
                'Time':            op['Time'],
                'Page_Number':     page['page_number'],
            })

    return master_rows, flagged_rows