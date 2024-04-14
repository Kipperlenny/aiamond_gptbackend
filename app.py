from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
import requests
import uuid
from openai import OpenAI

app = Flask(__name__)
load_dotenv()

GPT3_MODEL = os.getenv('GPT3_MODEL')
GPT4_MODEL = os.getenv('GPT4_MODEL')

# Store conversations in memory for simplicity
conversations = {}

client = OpenAI()

@app.route('/start_conversation', methods=['POST'])
def start_conversation():
    data = request.json
    title = data.get('title', '')  # Get the title from the request data, default to an empty string if not provided

    conv_id = str(uuid.uuid4())
    conversations[conv_id] = {"title": title, "history": []}  # Store the title and the conversation history in a dictionary

    return jsonify({"conversation_id": conv_id}), 201

def summarize_conversation(conv_id):
    # Get the conversation history
    conversation_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversations[conv_id]])

    # Call the summarization API
    summary = client.chat.completions.create(
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
    ).choices[0].message['content']  # Get the content of the response

    # Replace the conversation history with the summary
    conversations[conv_id] = [{"role": "system", "content": summary}]

@app.route('/add_to_conversation', methods=['POST'])
def add_to_conversation():
    data = request.json
    conv_id = data.get('conversation_id')
    question = data.get('question')

    # If conv_id is not provided or doesn't exist, start a new conversation
    if not conv_id or conv_id not in conversations:
        conv_id = str(uuid.uuid4())
        title = question[:255]  # Get the first 255 characters from the question as the title
        conversations[conv_id] = {"title": title, "history": []}

    response = send_to_gpt4(question, conv_id)

    # Add the user's question to the conversation history
    conversations[conv_id]["history"].append({"role": "user", "content": question})

    # Add the assistant's response to the conversation history
    conversations[conv_id]["history"].append({"role": "assistant", "content": response})

    # If the conversation history exceeds a certain length, summarize it
    if len(conversations[conv_id]["history"]) > 10:  # Change this to the desired limit
        summarize_conversation(conv_id)

    return jsonify({"response": response, "conversation_id": conv_id}), 200

@app.route('/list_conversations', methods=['GET'])
def list_conversations():
    conv_list = [{"id": conv_id, "title": conv["title"]} for conv_id, conv in conversations.items()]
    return jsonify(conv_list), 200

@app.route('/get_conversation/<conv_id>', methods=['GET'])
def get_conversation(conv_id):
    if conv_id in conversations:
        return jsonify(conversations[conv_id]["history"]), 200
    else:
        return jsonify({"error": "Conversation not found"}), 404
    
@app.route('/delete_conversation/<conv_id>', methods=['DELETE'])
def delete_conversation(conv_id):
    if conv_id in conversations:
        del conversations[conv_id]
        return jsonify({"message": "Conversation deleted"}), 200
    else:
        return jsonify({"error": "Conversation not found"}), 404

# https://platform.openai.com/docs/api-reference/chat/create
def send_to_gpt4(question, conv_id):
    # Get the conversation history
    conversation_history = conversations[conv_id]["history"]

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
    import logging
    logging.basicConfig(filename='error.log', level=logging.DEBUG)
    app.run(debug=True)