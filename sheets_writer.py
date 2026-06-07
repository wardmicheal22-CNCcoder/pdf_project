import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# -- Config ------------------------------------
# Paste your Spreadsheet ID here
SPREADSHEET_ID = '1Nu8ynRnYhwRKBX44FP1CG5domsL-0SEA-OoH2AsSirg'