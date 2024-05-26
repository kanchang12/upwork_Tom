from flask import Flask, render_template, jsonify, request
import requests

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/send_message', methods=['POST'])
def send_message():
    # Get user input from the request
    user_input = request.json['message']
    
    # Simulate sending user input to webhook and receiving response
    response_from_webhook = send_to_webhook(user_input)
    
    # Send the response back to the HTML page
    return jsonify({'response': response_from_webhook})

def send_to_webhook(user_input):
    # URL of the webhook
    webhook_url = 'https://hook.eu2.make.com/xu9opvhl51s6n840q920bplnx5y6ixpt'

    # Send user input to webhook and receive response
    response = requests.post(webhook_url, json={'message': user_input})
    
    # Check if request was successful
    if response.status_code == 200:
        return response.json()['response']
    else:
        return 'Error: Webhook request failed'

if __name__ == '__main__':
    app.run(debug=True)
