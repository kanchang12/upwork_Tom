import os
from flask import Flask, render_template, request, jsonify, redirect, session, url_for
import openai
import requests
from fuzzywuzzy import fuzz

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your_secret_key')

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

# Define function to fetch email data
def fetch_email_data(query):
    access_token = session.get('access_token')
    if not access_token:
        return {"error": "Zoho authentication required. Please log in to Zoho."}

    headers = {
        'Authorization': f'Zoho-oauthtoken {access_token}'
    }
    # Use Zoho Mail API to search emails
    search_url = f'https://mail.zoho.com/api/accounts/{{account_id}}/messages/search?search_key={query}'
    response = requests.get(search_url, headers=headers)
    
    if response.status_code == 200:
        emails = response.json().get('data', [])
        email_data = []
        for email in emails:
            email_details = {
                'subject': email.get('subject', ''),
                'sender': email.get('from', ''),
                'body': email.get('body', ''),
                'datetime': email.get('datetime', ''),
                'attachments': email.get('attachments', [])
            }
            email_data.append(email_details)
        return {"emails": email_data}
    else:
        return {"error": f"Error fetching emails: {response.status_code}"}

# Define function for fuzzy search
def fuzzy_search(query, target_list):
    max_score = 0
    best_match = None
    for target in target_list:
        score = fuzz.partial_ratio(query.lower(), target.lower())
        if score > max_score:
            max_score = score
            best_match = target
    return best_match

def rephrase_command(user_command):
    prompt = f"User: \"{user_command}\"\nAI: Search for:"
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=30,
        temperature=0.5,
        stop="\n"
    )
    return response.choices[0].message['content'].strip()

def search_answer(user_input, answer_json):
    # Search for the user input in the answer JSON
    if user_input in answer_json:
        return answer_json[user_input]
    else:
        return "No relevant information found."

# Define Flask routes
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

            # Rephrase the user command using OpenAI
            rephrased_command = rephrase_command(user_message)

            # Extract the variable from the rephrased command
            variable = rephrased_command.split(":")[1].strip()

            email_data = fetch_email_data(variable)
            if email_data:
                response_text = email_data
            else:
                # Continue with the conversation using OpenAI's chat completion
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=conversation,
                    max_tokens=150
                )
                response_text = response['choices'][0]['message']['content']

            return jsonify({'answer': response_text})

        except Exception as e:
            return jsonify({"error": str(e)}), 400

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

if __name__ == "__main__":
    host = '0.0.0.0'
    port = int(os.environ.get('PORT', 5000))
    app.run(host=host, port=port)
