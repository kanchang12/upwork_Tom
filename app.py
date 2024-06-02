from flask import Flask, render_template, request, send_file
import base64
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import os
import io

app = Flask(__name__)

# Function to authenticate and build the Gmail API service
def get_gmail_service():
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        # Check if the token is valid
        if not creds.valid:
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                os.remove('token.json')
                creds = None
    
    if not creds:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=8080)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    service = build('gmail', 'v1', credentials=creds)
    return service

# Function to fetch the latest email based on a keyword
def fetch_latest_email(service, keyword):
    user_id = 'me'
    query = f'subject:{keyword}'
    result = service.users().messages().list(userId=user_id, q=query).execute()
    messages = result.get('messages', [])

    if not messages:
        return None

    latest_message_id = messages[0]['id']
    message = service.users().messages().get(userId=user_id, id=latest_message_id).execute()

    email_data = {
        'date': '',
        'sender': '',
        'subject': '',
        'body': '',
        'attachments': []
    }

    for header in message['payload']['headers']:
        if header['name'] == 'Date':
            email_data['date'] = header['value']
        elif header['name'] == 'From':
            email_data['sender'] = header['value']
        elif header['name'] == 'Subject':
            email_data['subject'] = header['value']

    parts = message['payload'].get('parts', [])
    for part in parts:
        if part['mimeType'] == 'text/plain':
            body = base64.urlsafe_b64decode(part['body']['data'].encode('UTF-8')).decode('UTF-8')
            email_data['body'] = body
        elif 'filename' in part and part['filename']:
            attachment = {
                'filename': part['filename'],
                'mimeType': part['mimeType'],
                'data': part['body']['attachmentId'],
                'messageId': latest_message_id
            }
            email_data['attachments'].append(attachment)

    return email_data

# Route to handle the main page and form submission
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        keyword = request.form['keyword']
        service = get_gmail_service()
        email_data = fetch_latest_email(service, keyword)

        if email_data:
            return render_template('index.html', email=email_data)
        else:
            return render_template('index.html', error="No email found")

    return render_template('index.html')

# Route to handle attachment downloads
@app.route('/download/<attachment_id>', methods=['GET'])
def download_attachment(attachment_id):
    message_id = request.args.get('message_id')
    service = get_gmail_service()
    attachment = service.users().messages().attachments().get(userId='me', messageId=message_id, id=attachment_id).execute()

    attachment_data = base64.urlsafe_b64decode(attachment['data'].encode('UTF-8'))

    return send_file(
        io.BytesIO(attachment_data),
        attachment_filename=f"{attachment_id}",
        as_attachment=True
    )

if __name__ == '__main__':
    app.run(debug=True)
