import requests
from flask import Flask, request, jsonify, render_template
import pymongo
import openai
import re
import sys
import os
from pymongo import MongoClient  # Ensure this import is present
from pymongo.errors import ServerSelectionTimeoutError


app = Flask(__name__)

MONGODB_URI = "mongodb+srv://kanchang12:Ob3uROyf8rtbEOwx@cluster0.sle630c.mongodb.net/upwrok?retryWrites=true&w=majority&ssl=true"
MONGODB_DB_NAME = "upwrok"
MONGODB_COLLECTION_NAME = "files"

# Initialize MongoDB client with SSL parameters
client = MongoClient(MONGODB_URI, ssl_cert_reqs='CERT_NONE')  # Use 'CERT_REQUIRED' for stricter verification
db = client.get_database(MONGODB_DB_NAME)
collection = db.get_collection(MONGODB_COLLECTION_NAME)

def read_files_from_database(collection):
    try:
        cursor = collection.find()
        for doc in cursor:
            print(doc)  # Or process the document as needed
        return cursor
    except ServerSelectionTimeoutError as err:
        print("Error reading from MongoDB:", err)
        return []

def update_aggregate_text():
    aggregated_text = read_files_from_database(collection)
    return aggregated_text







@app.route('/')
def index():
    return render_template('index.html')



openai_api_key = os.getenv("OPENAI_API_KEY")
client = openai.Client(api_key=openai_api_key)



def get_claude_response(user_input):

    aggregated_text = update_aggregate_text()

    system_instructions = f"""
    You are an assistant of a business owner.

    Understand user intent and answer
    tell me the names of the properties at New Jersey
    You will give all the names. Don't ask to confirm again. If user asks something answer!! Don't asks questions
    Your job is to give to the point answers to him to help in the business
    for that you have primary options your system instructions and the data in the variable {aggregated_text}
    If any data is not there, you will found the data in your public training data, and provide an answer
    All your answers should be to the point and maximum of 15 words. If user asks for the cleaner answer only the cleaner name and nothing else
    This is how you will answer:
    WHEN THE USER WILL SEND A QUESTION, YOU WILL FIRST CLASSIFY THAT IN FOUR CATEGORIES
    ADD RECORD UPDATE RECORD SET ALERT FETCH RECORD

    You will give space between the words and not new line characters
    FETCH RECORD\n\nLocation: Brick\nType: Vacation Rentals\nAddress: 58 E Coral DR Brick NJ\nRoom setup: 2 Guest House units\n\nDo you need more details?

    This is a very bad way to provide data

    UNDERSTand user intent based on user question and asnwer accordingly

    Please avoid them and give spaces between the words instead

    IF FETCH RECORD:
    You will read the data and answer in max 15 words. You will give answer which a business owner can use. 
    If how many properties are there
    YOu will tell how many and ask if he wants the names? That's all
    If asked at this property who is cleaner or contractor, you will give the correct name
    If asked, how many properties are in New Jersey, you will calculate and answer the number
    If asked how far is the property from airport, you will find the address calculate the distance and let user know
    if user asks how many properties are there and you said 1 and user asks what is the name. You will answer the name of that one property
    If user asks to update a record
    and then asks for the same value again, you will give the updated record
    Please undertsand the context
    'what are the properties we have at New Jersey

    We have properties in New Jersey. Would you like to know the names of the properties?
    yes that is what I asked what are the properties
    There are multiple properties. Do you want the names of all properties?'
    here clearly user is asking for the names of the properties, so your twice questioning is annoying and wrong. You need to understand the intent and answer
    No irrelevant answers please

    'what are the properties we have at New Jersey
We have properties in New Jersey. Would you like to know the names of the properties?
yes I do
What specific information or task would you like assistance with for your business?'

It is clearly when user is saying yes I do, he wants to know the names. So give him the names. Your question is irrelevant

The nearest property to the airport in New Jersey is located at [Address].

Give value read the system instruction understand user intent find answer and gve proper answer

what are the properties there
We have multiple properties. Would you like to know the names of all properties?
yes I want all New Jersey properties
We have multiple properties in New Jersey. Would you like the names of all properties? This is wrong answer: Give all the names

    If the classification is UPDATE RECORD
    You will return
    UPDATE RECORD File name *Variable name* New Value
    The variable name should be in ** enclosed

    So If the user says, change the employee in Brics property to Tom
    You wil return
    UPDATE RECORD Brick *Employee Name* Tom

    The variable must be enclosed in * *

    You will give space between the words and not new line characters

    Now these are the variable names
    If the user can't say the right variable name, it is your duty to understand what he is saying and find the correct value
    So Phone number is same as *cell number*, *cell no*, cell *phone number* and what not
    if user says employee that can be employee name also

    Location
    Type
    Address
    Room setup
    Employee name
    Employee  role
    Cell phone
    Talk route
    Facebook link
    Garbage day
    Platforms advertised
    Cleaners info
    Property checker
    Pool cleaner
    Lawn Maintenance
    Furniture cleaner
    Hvac contractor : Assured 
    Plumbing contractor
    Electrical contractor
    contractor
    Appliance contractor
    Insurance
    Electric bill
    Water bill
    Gas bill
    Internet bill
    Mortgage

    If the user can't say the right variable name, it is your duty to understand what he is saying and find the correct value
    So Phone number is same as cell number, cell no, cll phone number and what not
    However, please give coherent reply
    When I am asking for employee name but did not mention the property
    You asked the property name in next line and I provided the same
    That means employee name for that property. DO NOT Ask to confirm the employee name as user has already said that like this

    Also the property name you will check with all properties
    So if the users asks Sicklerville but mispronounced it, you will do two things
    If it's understandable, return that; if not, ask for clarification.
    """

    message = client.chat.completions.create(
        model="gpt-3.5-turbo-16k",
        messages=[
            {"role": "system", "content": system_instructions},
            {"role": "user", "content": user_input}
        ],
        temperature=1,
        max_tokens=2560,
        top_p=1,
        frequency_penalty=0.9
    )

    generated_text = message.choices[0].message.content
    print("1", generated_text)
    return generated_text
    
    # Search in specific files
    response = search_in_specific_files(user_input)
    return response


def find_best_match(partial_name, valid_names):
    for name in valid_names:
        if partial_name in name:
            return name
    return " "


@app.route('/process_command', methods=['POST'])
def process_command():
    user_input = request.json.get('user_input')

    try:
       aggregated_text = update_aggregate_text()
       claude_response = get_claude_response(user_input)
       return jsonify({"response": claude_response})
    except Exception as e:
        print("Error processing command:", e)
        return jsonify({"error": str(e)}), 500

    # Get response from OpenAI based on aggregated text
    claude_response = get_claude_response(user_input)

    # Check if the response is a simple message
    if "FETCH RECORD" not in claude_response and "UPDATE RECORD" not in claude_response:
        # Return the response as is
        return jsonify({"extracted_text": claude_response})

    # Handle specific actions
    results = []
    words = []

    # Split response by space and process each word, treating words enclosed in * as single words
    pattern = re.compile(r'\*(.*?)\*|(\S+)')
    words = [match.group(1) or match.group(2) for match in pattern.finditer(claude_response)]

    print(f"Words extracted: {words}")  # Debug: Print extracted words

    i = 0
    while i < len(words):
        action = words[i].strip()
        print(f"Action: {action}")  # Debug: Print current action
        i += 1
        if i < len(words):
            args = words[i].strip()
            print(f"Args: {args}")  # Debug: Print current arguments
            if action == 'FETCH' and (args == 'RECORD' or not args):
                # Handle FETCH RECORD if needed
                result = claude_response
                results.append(result)
            elif action == 'UPDATE' and args == 'RECORD':
                print("In UPDATE RECORD block")  # Debug: Print update record block entry
                if i + 2 < len(words):  # Check if there are enough words
                    file_name = words[i+1]
                    variable_name = words[i + 2]
                    new_value = ' '.join(words[i + 3:])
                    print(f"File name: {file_name}")  # Debug: Print file name
                    print(f"Variable name: {variable_name}")  # Debug: Print variable name
                    print(f"New value: {new_value}")  # Debug: Print new value

                    # Call update_record function
                    result = update_record(db, file_name, variable_name, new_value)

                    results.append(result)
                    i += 3 + len(new_value.split())  # Move to the next action
                else:
                    result = 'Invalid arguments for UPDATE RECORD'
                    results.append(result)
                    i += 3  # Move to the next action even if it's invalid
            elif action == 'ADD' and args == 'RECORD':
                pass  # Handle ADD RECORD similarly
            elif action == 'ADD' and args == 'ALERT':
                pass  # Handle ADD ALERT similarly
            elif action == 'EXECUTE' and args == 'ALERT':
                pass  # Handle EXECUTE ALERT similarly
            else:
                pass
        i += 1

    # Prepare response
    response_text = '\n'.join(results)
    response_json = {"extracted_text": response_text}
    return jsonify(response_json)


import re

def update_record(db, file_name, variable_name, new_value):
    collection = db[MONGODB_COLLECTION_NAME]

    # Find the document with the given file name
    doc = collection.find_one({"filename": file_name})
    if not doc:
        return f"File {file_name} not found in the database"

    # Check if the variable name exists directly in the keys
    if variable_name in doc:
        matched_variable = variable_name
        old_value = doc[variable_name]
    else:
        # Search within the content field for the variable name
        matched_variable = None
        content = doc.get("content", "")
        for line in content.split("\n"):
            if variable_name.lower() in line.lower():
                matched_variable = line.split(":")[0].strip()
                # Extract old value if found
                old_value = line.split(":")[1].strip()
                break

    if not matched_variable:
        return f"Variable {variable_name} not found in file {file_name}"

    # Update the document with the new value and previous value
    if "Previous value" in doc.get("content", ""):
        new_content = doc["content"].replace(f"Previous value = \"{old_value}\"", f"Previous value = \"{old_value}\"\n{matched_variable}: {new_value}")
    else:
        new_content = doc["content"].replace(f"{matched_variable}: {old_value}", f"{matched_variable}: {new_value}\nPrevious value = \"{old_value}\"")

    # Update the document with the new content
    collection.update_one(
        {"_id": doc["_id"]},
        {"$set": {"content": new_content}}
    )

    return f"Updated {file_name}: {matched_variable} set to {new_value}, Previous value = \"{old_value}\""




if __name__ == '__main__':
    app.run(debug=True)

