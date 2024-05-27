from flask import Flask, render_template, jsonify, request
import requests
import second

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/send_message', methods=['POST'])
def send_message():
    try:
        # Get the JSON data from the request
        data = request.get_json()
        
        # Print the received JSON data to the console
        print("Received JSON data:", data)
        
        # Process the data using functions from second.py
        processed_data = second.process_data(data)
        
        # Send processed data to Make.com webhook and receive response
        response_from_webhook = send_to_webhook(processed_data)
        
        # Send the response back to the HTML page
        return jsonify({'status': 'success', 'response': response_from_webhook})
    except Exception as e:
        print("Error:", str(e))
        return jsonify({'status': 'error', 'message': str(e)}), 400

def send_to_webhook(data):
    # URL of the Make.com webhook
    webhook_url = 'https://hook.eu2.make.com/xu9opvhl51s6n840q920bplnx5y6ixpt'

    # Send user input to webhook and receive response
    response = requests.post(webhook_url, json=data)
    
    # Check if request was successful
    if response.status_code == 200:
        # Check if the response is in JSON format
        try:
            return response.json()
        except ValueError:
            return 'Error: Response is not in JSON format'
    else:
        return 'Error: Webhook request failed'

if __name__ == '__main__':
    app.run(debug=True)
