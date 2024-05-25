import os
from flask import Flask, request, redirect, session, jsonify
import requests

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your_secret_key')

# Zoho OAuth2 configuration
ZOHO_CLIENT_ID = os.getenv('ZOHO_CLIENT_ID')
ZOHO_CLIENT_SECRET = os.getenv('ZOHO_CLIENT_SECRET')
ZOHO_REDIRECT_URI = os.getenv('ZOHO_REDIRECT_URI', 'urn:ietf:wg:oauth:2.0:oob')
ZOHO_AUTHORIZATION_URL = 'https://accounts.zoho.com/oauth/v2/auth'
ZOHO_TOKEN_URL = 'https://accounts.zoho.com/oauth/v2/token'
ZOHO_SCOPES = 'ZohoMail.messages.READ'

@app.route("/talk", methods=["POST"])
def talk():
    if request.method == "POST":
        # User speaks to the bot
        user_input = request.json.get("user_input")
        response = f"User said: {user_input}"

        # Redirect the user to Zoho login for authorization
        auth_url = f'{ZOHO_AUTHORIZATION_URL}?response_type=code&client_id={ZOHO_CLIENT_ID}&redirect_uri={ZOHO_REDIRECT_URI}&scope={ZOHO_SCOPES}&access_type=offline&prompt=consent'
        return redirect(auth_url)

@app.route('/callback')
def callback():
    # Receive the authorization code from Zoho callback
    code = request.args.get('code')
    token_data = {
        'code': code,
        'client_id': ZOHO_CLIENT_ID,
        'client_secret': ZOHO_CLIENT_SECRET,
        'redirect_uri': ZOHO_REDIRECT_URI,
        'grant_type': 'authorization_code'
    }
    # Exchange the authorization code for access token
    token_response = requests.post(ZOHO_TOKEN_URL, data=token_data)
    tokens = token_response.json()

    # Store the access token in session
    session['access_token'] = tokens['access_token']
    session['refresh_token'] = tokens['refresh_token']

    # Return the access token in the JSON response
    return jsonify({'access_token': session['access_token']})


if __name__ == "__main__":
    app.run(debug=True)
