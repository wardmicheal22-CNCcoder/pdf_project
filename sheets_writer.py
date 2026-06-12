import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# -- Config ------------------------------------
# Paste your Spreadsheet ID here
SPREADSHEET_ID = '1Nu8ynRnYhwRKBX44FP1CG5domsL-0SEA-OoH2AsSirg'

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Column order for Master sheet - must match normalizer.py output
MASTER_HEADERS = [
    'Customer', 'WO_Number', 'Description',
    'WJ_Time', 'WJ_End_Date',
    'Lathe_Time', 'Lathe_End_Date',
    'Mill_Time', 'Mill_End_Date',
    'Finish_Date'
]

FLAGGED_HEADERS = [
    'WO_Number', 'Customer', 'Operation_Found', 'Time', 'End_Date', 'Page_Number'
]

DUPLICATE_HEADERS = [
    'WO_Number', 'Customer', 'Finish_Date', 'Skipped_Reason'
]


def get_service():
    """
    Handles Google authentication.
    First run opens a browser window to log in and saves a token.json file.
    Every run after that uses the saved token automatically — no browser needed.    
    """
    creds = None
   
    # token.json stores your login after the first run
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # If no valid credentials, prompt login in browser
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        # Save token so next run is automatic
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('sheets', 'v4', credentials=creds)


def get_existing_wo_numbers(service):
    """
    Reads column B (WO_Number) from the Master sheet
    and returns a set of all WO numbers already in the sheet.
    Used to detect duplicates before writing.
    """
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range='Master!B:B'
    ).execute()

    values = result.get('values', [])
    # Flatten the list and skip the header row
    return {row[0] for row in values[1:] if row}


def ensure_headers(service):
    """
    Checks if the Master sheet has headers yet.
    If the sheet is empty, writes the header row.
    Same for Flagged and Duplicates sheets
    """
    sheets = {
        'Master': MASTER_HEADERS,
        'Flagged': FLAGGED_HEADERS,
        'Duplicates': DUPLICATE_HEADERS,
    }

    for sheet_name, headers in sheets.items():
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f'{sheet_name}!A1:A1'
        ).execute()

        # If A1 is empty the sheet has no headers yet
        if not result.get('values'):
            service.spreadsheets().values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=f'{sheet_name}!A1',
                valueInputOption='RAW',
                body={'values': [headers]}
            ).execute()
            print(f"  Headers written to {sheet_name} sheet")


def append_rows(service, sheet_name, headers, rows):
    """
    Appends a list of row dicts to a sheet.
    Converts each dict to a list in the correct column order
    using the headers list as the map.
    """
    if not rows:
        return
    
    # Convert dicts to lists in the correct column order
    # If a key is missing from the dict, default to 'N/A'
    values = [
        [str(row.get(col, 'N/A')) for col in headers]
        for row in rows 
    ]

    service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=f'{sheet_name}!A1',
        valueInputOption='RAW',
        insertDataOption='INSERT_ROWS',
        body={'values': values}
    ).execute()


def write_to_sheets(master_rows, flagged_rows):
    """
    Main function called by main.py.
    Handles the full write process:
    1. Authenticate
    2. Ensure headers exist
    3. Check for duplicates
    4. Write new rows to master
    5. Write flagged ops to Flagged
    6. Write skipped duplicates to Duplicates
    """
    print("Connecting to Google Sheets...")
    service = get_service()

    # Make sure all three sheets have headers
    ensure_headers(service)

    # Get WO numbers already in the master sheet
    existing_wo_numbers = get_existing_wo_numbers(service)

    new_rows = []
    duplicate_rows = []

    # Sort master rows into new vs duplicate
    for row in master_rows:
        if row['WO_Number'] in existing_wo_numbers:
            duplicate_rows.append({
                'WO_Number': row['WO_Number'],
                'Customer': row['Customer'],
                'Finish_Date': row['Finish_Date'],
                'Skipped_Reason': 'WO already exists in Master sheet'
            })
            print(f"  ⚠ {row['WO_Number']} already exists — skipped")
        else:
            new_rows.append(row)

    # Write new rows to Master sheet
    if new_rows:
        append_rows(service, 'Master', MASTER_HEADERS, new_rows)
        print(f"  ✓ {len(new_rows)} WO(s) written to Master sheet")

    # Write flagged operations
    if flagged_rows:
        append_rows(service, 'Flagged', FLAGGED_HEADERS, flagged_rows)
        print(f"  ✓ {len(flagged_rows)} flagged operation(s) written to Flagged sheet")

    # Write duplicates log
    if duplicate_rows:
        append_rows(service, 'Duplicates', DUPLICATE_HEADERS, duplicate_rows)
        print(f"  ✓ {len(duplicate_rows)} duplicate(s) logged to Duplicates sheet")

    # Summary
    print(f"\nDone. {len(new_rows)} new, {len(duplicate_rows)} skipped, {len(flagged_rows)} flagged.")