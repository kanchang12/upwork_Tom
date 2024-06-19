from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
import cohere.client
from bson import json_util
import copy
import requests
import pymongo
from pymongo import MongoClient
import re

app = Flask(__name__)

MONGODB_URI = "mongodb+srv://kanchang12:Ob3uROyf8rtbEOwx@cluster0.sle630c.mongodb.net/upwrok?retryWrites=true&w=majority"
MONGODB_DB_NAME = "upwrok"
MONGODB_COLLECTION_NAME = "files"

client = MongoClient(MONGODB_URI)
db = client[MONGODB_DB_NAME]
properties_collection = db[MONGODB_COLLECTION_NAME]
important_notes_collection = db["important_notes"]
COHERE_API_KEY = os.getenv("COHERE_API_KEY")

cohere_client = cohere.Client(api_key=COHERE_API_KEY)

all_documents = list(properties_collection.find({}, {"_id": 0}))
document_dict = {doc.get('file_content', '').split('\n')[0].lower(): doc for doc in all_documents}

def get_gpt_response(user_input, conversation_history):
    property_summaries = [doc.get('file_content', '') for doc in document_dict.values() if 'property' in doc.get('file_content', '').split('\n')[0].lower()]
    other_summaries = [doc.get('file_content', '') for doc in document_dict.values() if 'property' not in doc.get('file_content', '').split('\n')[0].lower()]
    

    prompt = f"""
        You are Nia, a conversational AI assistant that can provide concise and natural responses to queries based on the provided context. You should be able to identify, count, and summarize relevant information from the context in a conversational manner, avoiding overly detailed or robotic responses.

        For example, if the user asks how many cleaners there are, you should check all the properties and count where cleaners' information is given.

        This will be done for all cases involving properties, employees, or any other relevant data.

        User's Query: {user_input}

        Don't ask stupid questions about context if user asks a simple request, do that or reply I don't have data
        everything give one line TO THE POINT ANSWER

        If the query is related to properties, please provide your response based on the context containing property summaries. If the query is not related to properties, please provide your response based on the context containing other summaries.

        IF the name is not clear check with property names and {json_util.dumps(property_summaries)} to get nearest
        so if you think someone calling big property, is actually maybe Brick property and so on
        Property Summaries Context: {json_util.dumps(property_summaries)}
    This is an example for update record type only. for rest follow your logic
        YOu MUST RETURN KEY WORD update record IF UPDATE RECORD IS ASKED. When specifically change or update or remove is asked not always For update
        understand the context and return these four values in this format
          read last few conversation to find the values of these four
            intent = update record
            property_name = (property in discussion)
        field_name = (the variable name in discussion)
        new_value = (The new value to updated)
        This is only for the cases where user explicitly expresses desire to update or change, not other cases
        Please don't change the format ever it should in four line no extra symbols just same as below
        
        intent = update record
        property_name = 
        field_name = 
        new_value = 
    you have to understand and respond
        Other Summaries Context: {json_util.dumps(other_summaries)}
    """

    response = cohere_client.chat(
        message=prompt,
        model="command-r-plus",
        temperature=0.7,
        frequency_penalty=0,
        presence_penalty=0,
        prompt_truncation='AUTO'
    )

    generated_text = response.text
    print(generated_text)
    return generated_text


# Define all MongoDB field names
mongo_db_field_names = [
    "Location",
    "Type",
    "Address",
    "Room setup",
    "Employee name",
    "Employee  role",
    "Cell phone",
    "Talk route",
    "Facebook link",
    "Garbage day",
    "Platforms advertised",
    "Cleaners info",
    "Property checker",
    "Pool cleaner",
    "Lawn Maintenance",
    "Furniture cleaner",
    "Hvac contractor",
    "Plumbing contractor",
    "Electrical contractor",
    "Appliance contractor",
    "Insurance",
    "Electric bill",
    "Water bill",
    "Gas bill",
    "Internet bill",
    "Mortgage"
]



import re



def update_record(property_name, field_name, new_value):
    client = MongoClient(MONGODB_URI)
    db = client[MONGODB_DB_NAME]
    collection = db[MONGODB_COLLECTION_NAME]

    # Find the document where the file_content contains the property_name
    property_name = property_name.split(':')[0]
    print("at update property name split", property_name)
    regex_pattern = re.compile(fr"{re.escape(property_name)}", re.IGNORECASE)
    doc = collection.find_one({"file_content": {"$regex": regex_pattern}})

    if doc:
        # Extract the file name from the first line of the file_content field
        found_file_name = doc.get("file_content", "").split("\n")[0]
        print(f"Found File Name: {found_file_name}")

        # Split the file_content into lines
        file_content_lines = doc["file_content"].split("\n")

        # Find the line containing the field_name
        field_name = field_name.split(':')[0].strip()
        found_field_line = None
        for line in file_content_lines:
            if line.startswith(field_name + ":") or line.startswith(field_name + "\t"):
                found_field_line = line.split(':')[0].strip()
                break

        print(f"Found Field Name: {found_field_line}")

        if found_field_line:
            # Update the line containing the field_name
            updated_lines = []
            for line in file_content_lines:
                if line.startswith(found_field_line + ":") or line.startswith(found_field_line + "\t"):
                    key, old_value = line.split(":", 1)
                    updated_line = f"{key}:{new_value}"
                    updated_lines.append(updated_line)
                    updated_lines.append(f"Previous value:{old_value.strip()}")
                else:
                    updated_lines.append(line)

            updated_file_content = "\n".join(updated_lines)

            # Update the document with the updated file content
            collection.update_one(
                {"file_content": doc["file_content"]},
                {"$set": {"file_content": updated_file_content}}
            )
            print(f"Updated '{found_field_line}' to '{new_value}' for file '{found_file_name}'")

        else:
            print(f"Field '{field_name}' not found in the document.")
    else:
        print(f"File '{property_name}' not found in the database.")

    response_text = f"Updated '{found_field_line}' to '{new_value}' for file '{found_file_name}'"
    return response_text



def update_consolidated_data():
    global consolidated_data
    consolidated_data = list(properties_collection.find({}, {"_id": 0}))

def process_query(query):
    update_consolidated_data()
    result_response = get_gpt_response(query, "")
    important_note_phrases = ["save note", "save important note", "important note", "save note", "save important note"]

    if any(phrase in query.lower() for phrase in important_note_phrases):
        important_notes_collection.insert_one({"note": result_response})
        response_text = "Important note saved."
    else:
        response_text = result_response

    property_name = ""
    field_name = ""
    new_value = ""

    if "update record" in result_response.lower():
        print("update record")
        print(result_response)
        # Split the response into lines
        # Split the response into lines
        lines = result_response.strip().split('\n')

        # Initialize variables to store extracted values
        for line in lines:
            if line.startswith("property_name"):
                property_name = line.split(" = ")[1].strip()
            elif line.startswith("field_name"):
                field_name = line.split(" = ")[1].strip()
            elif line.startswith("new_value"):
                new_value = line.split(" = ")[1].strip()

        response_text = update_record(property_name, field_name, new_value)

    #append_new_conversation(conversation_history)

    return response_text


@app.route('/query', methods=['POST'])
def handle_query():
    data = request.json
    query = data.get('query')
    response_text = process_query(query)
    return jsonify({'response': response_text})

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    
    app.run(debug=True)
