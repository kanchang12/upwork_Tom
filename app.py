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
preset_instruction = "Consider yourself as executive assistant of Mr Tom. You will receive the command from him and search the mail box kanchan@ikanchan.com to return the data. If nothing is found you will inform that. If more than one instance is found, give the latest one, unless otherwise mentioned."

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

def search_emails(query):
    access_token = session.get('access_token')
    if not access_token:
        return "Zoho authentication required. Please log in to Zoho."

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

