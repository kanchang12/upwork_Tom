import os
from flask import Flask, render_template, request, jsonify, redirect, session, url_for
import openai
import requests
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your_secret_key')

# Set up OpenAI API key from environment variable
openai.api_key = os.getenv('OPENAI_API_KEY')

# Zoho OAuth2 configuration
ZOHO_CLIENT_ID = os.getenv('ZOHO_CLIENT_ID')
ZOHO_CLIENT_SECRET = os.getenv('ZOHO_CLIENT_SECRET')
ZOHO_REDIRECT_URI = os.getenv('ZOHO_REDIRECT_URI', 'https://scared-terrijo-webpagegem-c993c1c0.koyeb.app/zoho/callback')
ZOHO_AUTHORIZATION_URL = 'https://accounts.zoho.com/oauth/v2/auth'
ZOHO_TOKEN_URL = 'https://accounts.zoho.com/oauth/v2/token'
ZOHO_SCOPES = 'ZohoMail.messages.READ'

# Preset instruction for the agent
preset_instruction = """Consider yourself as the executive assistant of Mr. Tom Rose. He has a passcode "New York City".
When he will talk to you, you will ask him to verify the passcode. If he succeeds, then only you will proceed further.
You have given exclusive access to zoho email box kanchan@ikanchan.com. The client App has been created and client id and client secret is integrated with your backend.
For this email, you are directed to read email body, read pdf attachment and access like a super admin.
If Mr. Tom asked you to find a particular email, you will search and return the proper data.
Remember, the account access has been exclusively given to you to act as executive assistant.
If you can't find anything, you will reply that.
If you find many, you will return the latest one.
Also, if you are asked to fetch a data, you will search and respond automatically.
Your session should run until you are responding."""

@app.route("/")
def index():
    return render_template("index.html")

def rephrase_command(user_command):
    prompt = f"User: \"{user_command}\"\nAI: Search for:"
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=30,
            temperature=0.5,
            stop=["\n"]
        )
        # Print the entire response for debugging purposes
        print("Rephrase Command Response:", response)
        # Ensure choices are available before accessing
        if response['choices'] and len(response['choices']) > 0:
            return response['choices'][0]['message']['content'].strip()
        else:
            return "Error: No choices in response"
    except Exception as e:
        return f"Error: {str(e)}"

def fetch_email_data(search_term):
    if 'access_token' not in session:
        return redirect(url_for('zoho_login'))

    access_token = session['access_token']
    ZOHO_ACCOUNT_ID = '60003473422'  # Replace with your Zoho Mail account ID

    # Check if the access token is expired and refresh if necessary
    expires_at = session.get('expires_at')
    if expires_at and datetime.utcnow() > expires_at:
        refresh_access_token()

    headers = {
        'Authorization': f'Zoho-oauthtoken {session["access_token"]}'
    }
    search_url = f'https://mail.zoho.in/api/accounts/{ZOHO_ACCOUNT_ID}/messages/search?search_key={search_term}'
    response = requests.get(search_url, headers=headers)
    
    if response.status_code == 200:
        emails = response.json().get('data', [])
        if emails:
            latest_email = emails[0]  # Assuming the first email in the response is the latest one
            return {
                "subject": latest_email['subject'],
                "sender": latest_email['from']['address'],
                "body": latest_email['snippet'],
                "date": latest_email['date']
                # Add more fields as required
            }
        else:
            return "No relevant emails found."
    else:
        return f"Error fetching emails: {response.status_code}"

@app.route("/process_text", methods=["POST"])
def process_text():
    if request.method == "POST":
        try:
            conversation = request.json.get('conversation', [])

            # Check if conversation is empty or doesn't contain user messages
            if not conversation or not any(msg['role'] == 'user' for msg in conversation):
                return jsonify({'answer': "Error: Conversation is empty or doesn't contain user messages."})

            # Get the last user message from the conversation
            user_message = next(msg['content'] for msg in reversed(conversation) if msg['role'] == 'user')

            # Rephrase the user command using OpenAI
            rephrased_command = rephrase_command(user_message)
            print("Rephrased Command:", rephrased_command)  # Debugging: print the rephrased command

            # Check if rephrased_command is empty or contains an error
            if not rephrased_command:
                return jsonify({'answer': "Error: Empty rephrased command."})
            elif rephrased_command.startswith("Error:"):
                return jsonify({'answer': rephrased_command})

            # Extract the variable from the rephrased command
            try:
                variable = rephrased_command
            except IndexError:
                return jsonify({'answer': "Error: Unable to parse the rephrased command."})

            email_data = fetch_email_data(variable)
            if email_data:
                response_text = email_data
            else:
                # Continue with the conversation using OpenAI's chat completion
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo-16k",
                    messages=conversation,
                    max_tokens=150
                )
                print("Chat Completion Response:", response)  # Debugging: print the response
                if response and response['choices']:
                    response_text = response['choices'][0]['message']['content']
                else:
                    response_text = "No response from the model."

            return jsonify({'answer': response_text})

        except Exception as e:
            return jsonify({"error": str(e)}), 400

@app.route('/login/zoho')
def zoho_login():
    auth_url = f'{ZOHO_AUTHORIZATION_URL}?response_type=code&client_id={ZOHO_CLIENT_ID}&redirect_uri={ZOHO_REDIRECT_URI}&scope={ZOHO_SCOPES}&access_type=offline&prompt=consent'
    return redirect(auth_url)

@app.route('/zoho/callback')
def zoho_callback():
    code = request.args.get('code')
    token_data = {
        'code': code,
        'client_id': ZOHO_CLIENT_ID,
        'client_secret': ZOHO_CLIENT_SECRET,
        'redirect_uri': ZOHO_REDIRECT_URI,
        'grant_type': 'authorization_code'
    }
    token_response = requests.post(ZOHO_TOKEN_URL, data=token_data)
    tokens = token_response.json()
    session['access_token'] = tokens['access_token']
    session['refresh_token'] = tokens['refresh_token']
    # Calculate the expiration time
    session['expires_at'] = datetime.utcnow() + timedelta(seconds=int(tokens['expires_in']))
    return redirect(url_for('index'))

def refresh_access_token():
    refresh_token = session.get('refresh_token')
    token_data = {
        'refresh_token': refresh_token,
        'client_id': ZOHO_CLIENT_ID,
        'client_secret': ZOHO_CLIENT_SECRET,
        'grant_type': 'refresh_token'
    }
    token_response = requests.post(ZOHO_TOKEN_URL, data=token_data)
    tokens = token_response.json()
    session['access_token'] = tokens['access_token']
    session['expires_at'] = datetime.utcnow() + timedelta(seconds=int(tokens['expires_in']))

if __name__ == "__main__":
    host = '0.0.0.0'
    port = int(os.environ.get('PORT', 5000))
    app.run(host=host, port=port)
