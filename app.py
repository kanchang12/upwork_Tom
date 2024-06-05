from flask import Flask, render_template, request, jsonify
import requests
import os
import time

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with your secret key

# Replace with your Make.com webhook endpoint
MAKE_COM_ENDPOINT = 'https://hook.eu2.make.com/kv24kv7cddrvnuundv60a7mdk99lmxsu'

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_input = request.form['message']
        
        # Send a POST request to Make.com with user input
        make_response = requests.post(MAKE_COM_ENDPOINT, json={'message': user_input})
        app.logger.info(f"Response status code from Make.com: {make_response.status_code}")
        
        # Artificial delay to simulate processing time
        time.sleep(10)
        
        # Your middle activity goes here
        
        # Example of Claude usage (replace with your logic)
        response_content = "Your response from the middle activity"
        
        return jsonify({"user_input": user_input, "response": response_content})
    
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(debug=True)
