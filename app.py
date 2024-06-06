import requests
from flask import Flask, request, jsonify, render_template
import anthropic
import sys
import os


app = Flask(__name__)

MONGODB_API_URL = "https://eu-west-2.aws.data.mongodb-api.com/app/data-adgmytr/endpoint/data/v1/action/findOne"
MONGODB_API_KEY = os.getenv('Mongo_API')



DOCUMENTS = {
    "Sicklerville.docx": "_id 66618e8e367ca0e0be2fb776 \nfilename Sicklerville\nfile_type docx"
}

def save_chat_history(transcript):
    data = {"classification": "CHAT HISTORY", "transcript": transcript}
    headers = {'Content-Type': 'application/json', 'api-key': MONGODB_API_KEY}
    response = requests.post(MONGODB_API_URL, json=data, headers=headers)
    return response.json()

import requests

def fetch_record(file_name, variable_name):
    print("in mongo")
  
    
    # MongoDB API request payload
    payload = {
    "collection": "upworktom",
    "database": "upwrok",
    "dataSource": "Cluster0",
    "projection": {
        "_id": 0,
        "filename": file_name,
        "content": 1
    },
    }
        
    # MongoDB API headers
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Request-Headers': '*',
        'api-key': MONGODB_API_KEY,
    }
    
    # MongoDB API URL
    url = MONGODB_API_URL
    
    # Send request to MongoDB API
    response = requests.post(url, headers=headers, json=payload)
    
    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()
        content = data.get('document', {}).get('content', '')

        # Split content into lines
        lines = content.split('\n')

        # Initialize variable to store the value
        value = None

        # Search for the variable_name in each line
        for line in lines:
            # Split line by ':'
            parts = line.split(':')
            if len(parts) == 2:
                key = parts[0].strip()
                val = parts[1].strip()
                if key.lower() == variable_name.lower():  # Case-insensitive comparison
                    value = val
                    break
        print(value)

        if value is not None:
            return value
        else:
            return f"Variable '{variable_name}' not found in the document content."
    else:
        return f"Failed to fetch record: {response.text}"




def add_record(entity, name):
    # Placeholder function to add record
    pass

def update_record(entity, name):
    # Placeholder function to update record
    pass

def set_alert():
    # Placeholder function to set alert
    pass

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/process_command', methods=['POST'])
def process_command():
    user_input = request.json.get('user_input')
    
    # Get Claude response
    claude_response1 = get_claude_response(user_input)
    print("User Input:", user_input)
    print("Claude Response:", claude_response1)

    # Convert response items to text
    claude_response = [item.text for item in claude_response1 if hasattr(item, 'text')]
    
    # Process the response from Claude AI
    results = []
    for item in claude_response:
        if isinstance(item, str):
            lines = item.split('\n')
            if lines:
                action = lines[0].strip()
                args1 = lines[1:]  # Store the args in args1
                args_without_quotes = [arg.strip().strip('"') for arg in args1]  # Strip quotes from args
                args = [arg.replace('_', ' ') for arg in args_without_quotes]  # Replace underscores with spaces
                print("Action:", action)
                print("Args:", args)
                if 'FETCH' in action and 'RECORD' in action:
                    print("yes")
                    if len(args) >= 2:
                        file_name = args[0]
                        variable_name = args[1]
                        result = fetch_record(file_name, variable_name)
                elif action == 'UPDATE DOCUMENT':
                    # Handle UPDATE DOCUMENT similarly
                    pass
                elif action == 'ADD NEW RECORD':
                    # Handle ADD NEW RECORD similarly
                    pass
                elif action == 'ADD ALERT':
                    # Handle ADD ALERT similarly
                    pass
                elif action == 'EXECUTE ALERT':
                    # Handle EXECUTE ALERT similarly
                    pass
                elif action == 'TRAINING MANUAL':
                    result = fetch_record(args)
                    print(result)
                    return result
                else:
                    result = f'Unknown action: {action}'
                results.append(result)
            else:
                results.append('Empty response line')
        else:
            results.append(f'Invalid response item: {item}')

    print("Results:", results)

    return jsonify({'results': results, 'claude_response': claude_response})


def get_claude_response(user_input):
    print("in claude")
    client = anthropic.Anthropic(api_key = os.environ.get("ANTHROPIC_API_KEY"))
    message = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=1000,
        temperature=0,
        system="""
You are Nia. The AI bot for helping Interstate Properties.

Your first response would be: Hello I am Nia. How may I help you today?
Always!
You are an assistant of a python coder.
Your Only Job is to read the user input and prepare a output which can be fed into python code to retrieve data from MongoDB
If the user says, What is the property type of Sicklerville.
You will first make the classification

ADD RECORD
UPDATE RECORD
SET ALERT
FETCH RECORD


PLEASE NOTE

FIND RELEVANT VARIABLE

SO IF THE USER ASKS WHAT TYPE OF PROPERTY IS AVAILABLE

YOU WILL NOT REPLY PROPERTY-TYPE VARIABLE NOT PRESENT
TYPE IS PRESENT SO YOU WILL RETURN TYPE

IF USER ASKS WHO IS THE EMPLOYEE?

DON'T REPLY EMPLOYEE VARIABLE NT PRESENT

IF YOU SEE, EMPLOYEE NAME IS THERE, YOU WILL REPLY THAT

IF THE USER ASKS WHICH PROPERTY IS AVAILABLE

YOU WILL CHECK ALL AVAILABLE AND RETURN THE LATEST ONE ADDED

PLEASE BE VERY CAREFUL ABOUT THIS FACTOR

YOU WILL NEVER SAY THAT THE VARIABLE IS NOT AVAILABLE!!

NEVER!!!

YOU WILL UNDERSTAND THE QUESTION, CHECKK THE VARIABLE LIST AND RESPOND WITH THE BEST MATCH ANSWER

OR SAY: "SORRY, I DON'T HAVE THAT ANSWER"

THESE ARE THE VARIABLES:

Location 		: 
Type	    		: 
Address  		: 
Room setup		: 
Employee name	: 
Employee  role    	: 
Cell phone		: 
Talk route		:
Facebook link	:
Garbage day		:
Platforms advertised : 
Cleaners info 	: 
Property checker	:
Pool cleaner		:
Lawn Maintenance	: 
Furniture cleaner	:
Hvac contractor	: Assured 
Plumbing contractor	: 
Electrical contractor	: 
Drain cleaning	: 
contractor
Appliance contractor:	
Insurance		: 
Flood insurance	:
Electric bill		: 
Water bill		:
Gas bill		:
Internet bill		:
Mortgage	


IF USER SAYS PHONE CELL PHONE MOBILE NUMBER MOBILE PHONE OR ANY COMBINATION: IT WILL BE ONE ANSWER ONLY

PLEASE PLEASE MAKE SURE NOT TO SAY VARIABLE NOT AVAILABLE
UNDERSTAND FIND THE RELEVANT VALUE AND RETURN


So, here it will be FETCH RECORD
YOU MUST RETURN THREE THINGS

FETCH RECORD
DOCUMENT NAME
VARIABLE

LIKE FETCH RECORD
SICKLERVILLE
PLATFORMED ADVERTISED


Then find the variables
Sicklerville
location

you will ONLY return these to python code to process further
NO EXPLANATION
NO ADDITIONAL WORDS
NO ETHICAL DILEMMA OF READING OTHER STUFF
YOU GET A DATA, CLASSIFY AND RETURN CLASSIFICATION AND VARIABLE NAMES
THAT'S IT

User asked:
Hana has recently joined us. Add her in employee list



ADD RECORD
File name
variable name

ALSO

USER PRONOUCIATIONS CAN BE DIFFRENT SO CHECK THE FILE NAME HERE TOO ENSURE

Sicklerville

At present following are the documents:

_id 66618e8e367ca0e0be2fb776
filename "Sicklerville"
file_type "docx"

_id 6661905358f2ab5c0b3f5ed1
filename "Location-Cohost-Training-Manual_Reading"
file_type "docx"

Second task

After every chat, entire chat transcript to be given to Python file to save in a master file
classification would be CHAT HISTORY
CHAT HISTORY
<all the transcript>


If the user asks for update
call UPDATE RECORD

you will send the document name, the variable to change, existing value and the new value

So if the user says change the employee from Tom to James in the Red Banks Property

you will return

UPDATE RECORD
Red Banks
Employee
Tom
James

Only this nothing else

HOWEVER THIS IS DIFFERENT FOR TRAINING MANNUAL

TRAINING MANUAL:    Location-Cohost-Training-Manual_Reading

YOU WILL NOT LOOK FOR VARIABLES AND ANSWERS
FOR TRAINING MANUAL: YOU WILL SEARCH ALL THE TRAINING MANUALS, MAKE A NOTE OF MAXIMUM AROUND 30 WORDS, AND RETURN TO THE VARIABLE TRAINING_DATA

ACTION = TRAINING MANUAL

THAT'S IT!!

WHAT ARE THE STEPS TO DO IN FOR AIR BNB?
YOU WILL SEARCH, FIND SUMMARIZE AND RESPOND!

""",
        messages=[
            {"role": "user", "content": [{"type": "text", "text": user_input}]}
            
        ]
    )
    return message.content
    print(message.content)

def process_claude_response(response):

    pass
"""
    results = []
    for item in response:
        if isinstance(item, str):
            lines = item.split('\n')
            if lines:
                action = lines[0].strip()
                print("Action:", action)  # Debugging print
                args = [arg.strip("'") for arg in lines[1:] if arg.strip()]  # Remove single quotes and empty strings

                if 'FETCH' in action and 'RECORD' in action:
                    print("yes")
                    if len(args) >= 2:
                        file_name = args[0]
                        variable_name = args[1]
                        result = fetch_record(file_name, variable_name)
                        print(result)
                    else:
                        result = 'Invalid arguments for FETCH RECORD'
                elif action == 'CHAT HISTORY':
                    # Save chat history to master database
                    transcript = '\n'.join(args)
                    save_chat_history(transcript)
                    result = 'Chat history saved successfully'
                else:
                    result = f'Unknown action: {action}'
                results.append(result)
            else:
                results.append('Empty response line')
        else:
            results.append(f'Invalid response item: {item}')
    return results



    print("Results:", results)
    return results
"""
def find_best_match(partial_name, valid_names):
    for name in valid_names:
        if partial_name in name:
            return name
    return None

if __name__ == '__main__':
    app.run(debug=True)
