import os
from flask import Flask, render_template, request, jsonify, redirect, session, url_for
import openai
import requests
from fuzzywuzzy import fuzz

app = Flask(__name__)
# app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your_secret_key')

# Set up OpenAI API key from environment variable
openai.api_key = os.getenv('OPENAI_API_KEY')

# Zoho OAuth2 configuration
ZOHO_CLIENT_ID = os.getenv('ZOHO_CLIENT_ID')
ZOHO_CLIENT_SECRET = os.getenv('ZOHO_CLIENT_SECRET')
ZOHO_REDIRECT_URI = os.getenv('ZOHO_REDIRECT_URI', 'http://localhost:5000/zoho/callback')
ZOHO_AUTHORIZATION_URL = 'https://accounts.zoho.com/oauth/v2/auth'
ZOHO_TOKEN_URL = 'https://accounts.zoho.com/oauth/v2/token'
ZOHO_SCOPES = 'ZohoMail.messages.READ'

# Preset instruction for the agent
preset_instruction = """Consider yourself as the executive assistant of Mr. Tom Rose. He has a passcode "New York City".
When he will talk to you, you will ask him to verify the passcode. If he succeeds, then only you will proceed further.
You have given exclusive access to zoho email box kanchan@ikanchan.com. The client App has been created and client id and client secret is integrated with your backend.
For this email, you are directed to read email body, read pdf attachment and access like a super admin.
If Mr. Tom asked you to find a particular email, you will search and return the proper data.
Remember, the account access has been exclusively given to you to act as executive assistant
If you can't find anything, you will reply that
If you find many, you will return the latest one
Also, if you are asked to fetch a data, you will search and respond automatically.
Your session should run untill you are responding"""

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/process_text", methods=["POST"])
def process_text():
    if request.method == "POST":
        try:
            conversation = request.json.get('conversation', [])
            
            # Construct the initial system message based on the preset instruction
            if not any(msg['role'] == 'system' for msg in conversation):
                conversation.insert(0, {"role": "system", "content": preset_instruction})

            user_message = conversation[-1]['content']
            if "invoice" in user_message.lower():
                email_data = search_emails(user_message)
                response_text = email_data if email_data else "No relevant emails found."
            else:
                # Send the messages to OpenAI for chat completion
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo-16k",
                    messages=conversation,
                    max_tokens=150
                )

                # Get the response text from the model's response
                response_text = response['choices'][0]['message']['content']

            return jsonify({'answer': response_text})

        except Exception as e:
            return jsonify({"error": str(e)}), 400

def fuzzy_search(query, target_list):
    max_score = 0
    best_match = None
    for target in target_list:
        score = fuzz.partial_ratio(query.lower(), target.lower())
        if score > max_score:
            max_score = score
            best_match = target
    return best_match

@app.route('/login/zoho')
def zoho_login():
    auth_url = f'{ZOHO_AUTHORIZATION_URL}?response_type=code&client_id={ZOHO_CLIENT_ID}&redirect_uri={ZOHO_REDIRECT_URI}&scope={ZOHO_SCOPES}'
    return redirect(auth_url)
"""
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
    return redirect(url_for('index'))
"""
import requests

def authenticate_user_session():
    # Step 1: Get the code
    auth_url = "https://accounts.zoho.com/oauth/v2/auth"
    auth_params = {
        "scope": "ZohoMail.messages.READ",
        "client_id": "1000.ZCNMPBP0S2H5KC9A3SUUMUEBB1W4RK",
        "response_type": "code",
        "access_type": "offline",
        "redirect_uri": "http://127.0.0.1:5000/"
    }
    auth_response = requests.get(auth_url, params=auth_params)
    code = auth_response.json()['code']  # Extract the code from the response

    # Step 2: Exchange the code for an access token and refresh token
    token_url = "https://accounts.zoho.in/oauth/v2/token"
    token_data = {
        "code": code,
        "grant_type": "authorization_code",
        "client_id": "1000.ZCNMPBP0S2H5KC9A3SUUMUEBB1W4RK",
        "client_secret": "619c08c85dc95e7015b2f18045bf15c23812fff88d",
        "redirect_uri": "http://127.0.0.1:5000/",
        "scope": "ZohoMail.messages.READ"
    }
    token_response = requests.post(token_url, data=token_data)
    tokens = token_response.json()  # Extract the tokens from the response

    return tokens


def search_emails(query):
    access_token = session.get('access_token')
    if not access_token:
        tokens = authenticate_user_session()
        if 'access_token' in tokens:
            access_token = tokens['access_token']
            session['access_token'] = access_token
            session['refresh_token'] = tokens['refresh_token']
        else:
            return "Zoho authentication failed. Please try again."

    headers = {
        'Authorization': f'Zoho-oauthtoken {access_token}'
    }
    # Use Zoho Mail API to search emails
    search_url = f'https://mail.zoho.com/api/accounts/{{account_id}}/messages/search?search_key={query}'
    response = requests.get(search_url, headers=headers)
    
    if response.status_code == 200:
        emails = response.json().get('data', [])
        if emails:
            latest_email = emails[0]  # Assuming the first email in the response is the latest one
            return latest_email['snippet']  # Return the snippet or any relevant field
        else:
            return None
    else:
        return f"Error fetching emails: {response.status_code}"


if __name__ == "__main__":
    host = '0.0.0.0'
    port = int(os.environ.get('PORT', 5000))
    app.run(host=host, port=port)
