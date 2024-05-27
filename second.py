import os
import pickle
import base64
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from bs4 import BeautifulSoup

# Load JSON credentials content from environment variable
JSON_CREDS_CONTENT = os.environ.get('JSON_CREDS_CONTENT')
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def authenticate_gmail():
    creds = Credentials.from_authorized_user_info(json.loads(JSON_CREDS_CONTENT), SCOPES)
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            raise ValueError('Invalid credentials')
    service = build('gmail', 'v1', credentials=creds)
    return service

def search_emails(service, query):
    results = service.users().messages().list(userId='me', q=query).execute()
    messages = results.get('messages', [])
    return messages

def get_email_content(service, message_id):
    msg = service.users().messages().get(userId='me', id=message_id).execute()
    payload = msg['payload']
    parts = payload.get('parts', [])
    body = ""
    if parts:
        for part in parts:
            if part['mimeType'] == 'text/plain':
                body += base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
            elif part['mimeType'] == 'text/html':
                soup = BeautifulSoup(base64.urlsafe_b64decode(part['body']['data']).decode('utf-8'), 'html.parser')
                body += soup.get_text()
    else:
        body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
    return body

def find_specific_email(service, search_query):
    emails = search_emails(service, search_query)
    if not emails:
        print("No emails found.")
        return None
    email_contents = []
    for email in emails:
        body = get_email_content(service, email['id'])
        email_contents.append(body)
    return email_contents

if __name__ == '__main__':
    gmail_service = authenticate_gmail()
    search_query = "your search keywords"  # Set your search criteria here
    find_specific_email(gmail_service, search_query)
