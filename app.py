from flask import Flask, render_template, request, jsonify
import openai
import os
import requests

app = Flask(__name__)
openai.api_key = os.getenv('OPENAI_API_KEY')

POWER_AUTOMATE_ENDPOINT = 'https://hook.eu2.make.com/xu9opvhl51s6n840q920bplnx5y6ixpt'

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_input = request.form['message']
        
        # Send HTTP request to Make.com
        response = requests.post(POWER_AUTOMATE_ENDPOINT, json={'text': user_input})
        
        if response.status_code == 200:
            # If successful, return the response from Make.com
            make_response = response.json().get('response', 'Error: No response from Make.com')
            return jsonify({"user_input": user_input, "response": make_response})
        else:
            # If unsuccessful, return an error message
            return jsonify({"user_input": user_input, "response": f"Error: Failed to send message to Make.com (HTTP {response.status_code})"})
    
    except Exception as e:
        # Handle any errors to keep the conversation going
        error_message = 'Error: ' + str(e)
        return jsonify({"user_input": user_input, "response": error_message})

if __name__ == '__main__':
    app.run(debug=True)
