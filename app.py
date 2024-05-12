from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
import uuid
from openai import OpenAI
import boto3
from boto3.dynamodb.conditions import Key
import logging

logger = logging.getLogger()
logger.setLevel(logging.WARNING)

app = Flask(__name__)
CORS(app)
load_dotenv()

GPT3_MODEL = os.getenv('GPT3_MODEL')
GPT4_MODEL = os.getenv('GPT4_MODEL')

# Create a DynamoDB resource
dynamodb = boto3.resource('dynamodb')

# Get the table
conversations = dynamodb.Table('Conversations')

client = OpenAI()

@app.route('/api/start_conversation', methods=['POST'])
def start_conversation():
    data = request.json
    title = data.get('title', '')  # Get the title from the request data, default to an empty string if not provided

    conv_id = str(uuid.uuid4())
    conversations.put_item(
        Item={
            'id': conv_id,
            'title': title,
            'history': []
        }
    )

    return jsonify({"conversation_id": conv_id}), 201

def summarize_conversation(conv_id):
    # Get the conversation history
    response = conversations.get_item(Key={'id': conv_id})
    conversation = response['Item']
    conversation_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation['history']])

    # Call the summarization API
    response = client.chat.completions.create(
        model = GPT3_MODEL,
        messages=[
            {
            "role": "system",
            "content": "You are a helpful assistant that summarizes conversations for using them later as a chat history in the openai chat."
            },
            {
            "role": "user",
            "content": conversation_history
            }
        ],
        stream=False,
        temperature=0,
        max_tokens=2047,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    
    summary = response.choices[0].message.content  # Get the content of the response
    
    # Replace the conversation history with the summary
    conversations.update_item(
        Key={'id': conv_id},
        UpdateExpression='SET history = :val1',
        ExpressionAttributeValues={
            ':val1': [{"role": "system", "content": summary}]
        }
    )

def save_to_conversation(conv_id, role, content):
    # Add the message to the conversation history
    conversations.update_item(
        Key={'id': conv_id},
        UpdateExpression='SET history = list_append(history, :val1)',
        ExpressionAttributeValues={
            ':val1': [{"role": role, "content": content}]
        }
    )

def summarize_long_message(message):
    # Call the summarization API
    response = client.chat.completions.create(
        model = GPT3_MODEL,
        messages=[
            {
            "role": "system",
            "content": "You are a helpful assistant that summarizes long messages."
            },
            {
            "role": "user",
            "content": message
            }
        ],
        stream=False,
        temperature=0,
        max_tokens=2047,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    
    summary = response.choices[0].message.content  # Get the content of the response

    return summary

@app.route('/api/add_to_conversation', methods=['POST'])
def add_to_conversation():
    data = request.json
    conv_id = data.get('conversation_id')
    question = data.get('question')
    conversation = None

    # If conv_id is not provided or doesn't exist, start a new conversation
    if not conv_id:
        conv_id = str(uuid.uuid4())
        title = question[:255]  # Get the first 255 characters from the question as the title
        conversations.put_item(
            Item={
                'id': conv_id,
                'title': title,
                'history': []
            }
        )
        
        conversation = conversations.get_item(Key={'id': conv_id})['Item']
    else:
        conversation = conversations.get_item(Key={'id': conv_id})['Item']
        if not conversation:
            return jsonify({"error": "Conversation not found"}), 404

    # Check if the question is too long and summarize it if necessary
    if len(question) > 1000:  # Change this to the desired limit
        question = summarize_long_message(question)

    response = send_to_gpt4(question, conv_id)

    # Add the user's question to the conversation history
    save_to_conversation(conv_id, "user", question)

    # Add the assistant's response to the conversation history
    save_to_conversation(conv_id, "assistant", response)

    # If the conversation history exceeds a certain length, summarize the first part of it
    if conversation['history'] and len(conversation['history']) > 20:  # Change this to the desired limit
        summarize_conversation(conv_id)  # Summarize the first 10 messages

    # Get the updated conversation from the DynamoDB
    conversation = conversations.get_item(Key={'id': conv_id})['Item']

    return jsonify({"response": response, "conversation_id": conv_id, "conversation": conversation}), 200

@app.route('/api/list_conversations', methods=['GET'])
def list_conversations():
    # Scan the table to get all conversations
    response = conversations.scan()
    conv_list = [{"id": conv['id'], "title": conv['title']} for conv in response['Items']]
    return jsonify(conv_list), 200

@app.route('/api/get_conversation/<conv_id>', methods=['GET'])
def get_conversation(conv_id):
    # Get the conversation from the table
    response = conversations.get_item(Key={'id': conv_id})

    # If the conversation exists, return its history
    if 'Item' in response:
        return jsonify(response['Item']['history']), 200
    else:
        return jsonify({"error": "Conversation not found"}), 404

@app.route('/api/delete_conversation/<conv_id>', methods=['DELETE'])
def delete_conversation(conv_id):
    # Try to delete the conversation from the table
    response = conversations.delete_item(Key={'id': conv_id})

    # If the conversation was deleted, return a success message
    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        return jsonify({"message": "Conversation deleted"}), 200
    else:
        return jsonify({"error": "Conversation not found"}), 404
    
# https://platform.openai.com/docs/api-reference/chat/create
def send_to_gpt4(question, conv_id):
    response = conversations.get_item(
        Key={
            'id': conv_id
        }
    )
    conversation_history = response['Item']['history']

    # Format the conversation history for the system message
    formatted_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation_history])

    messages=[
        {
        "role": "system",
        "content": f"You are a helpful assistant. Be very short in answering, that means no friendly extra text etc. but only factual.\nConversation history:\n{formatted_history}"
        },
        {
        "role": "user",
        "content": f"{question}"
        }
    ]

    # print(messages)

    completion = client.chat.completions.create(
        model = GPT4_MODEL,
        messages=messages,
        stream=False,
        temperature=0,
        max_tokens=2047,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )

    return completion.choices[0].message.content

if __name__ == '__main__':
    app.run(debug=True)