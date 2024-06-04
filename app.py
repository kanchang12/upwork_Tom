from flask import Flask, render_template, request, jsonify
import openai
import os
import requests

app = Flask(__name__)
openai.api_key = os.getenv('OPENAI_API_KEY')

POWER_AUTOMATE_ENDPOINT = 'https://your-power-automate-endpoint'

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_input = request.form['message']
        
        # Send HTTP request to Power Automate
        response = requests.post(POWER_AUTOMATE_ENDPOINT, json={'text': user_input})
        bot_response = response.json().get('response', 'Error: No response from Power Automate')

        # Pass user input and bot response to OpenAI Chat API
        openai_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k",
            messages=[
                {
                    "role": "system",
                    "content":  "You are Sam. You will read user input and pass on the next phase for processing."
                },
                {
                    "role": "user",
                    "content": user_input
                }
            ],
            temperature=1,
            max_tokens=256,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )

        bot_response_from_openai = openai_response.choices[0].message['content']
        
        return jsonify({"user_input": user_input, "response": bot_response_from_openai})
    
    except Exception as e:
        # Handle any errors to keep the conversation going
        error_message = 'Error: ' + str(e)
        return jsonify({"user_input": user_input, "response": error_message})

if __name__ == '__main__':
    app.run(debug=True)
