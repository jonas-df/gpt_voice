#!/usr/bin/python3

import os
from groq import Groq
from dotenv import load_dotenv
import json


GREEN = "\033[32m"  # Green text
YELLOW = "\033[33m"  # Yellow text
RESET = "\033[0m"
TEXT_FILENAME = "transcribe_log.txt"
MESSAGES_JSON = "message.json"
INITIAL_MESSAGE = {
    "role": "system",
    "content": """
    You are a helpful assistant. 
    You will help me learn about programming. 
    I want you to act as a tutor giving hints 
    and links to resources rather than the answer
    right away.""",
}

# Load API credentials stored in .env file
load_dotenv()


# JSON helper functions
def initialize_messages():
    # Always overwrite the file with the initial message
    with open(MESSAGES_JSON, "w") as file:
        json.dump([INITIAL_MESSAGE], file, indent=4)
    print(f"{GREEN}messages.json has been initialized.{RESET}")


def append_json(file_path, role, content):
    try:
        with open(file_path, "r") as file:
            messages = json.load(file)
    except FileNotFoundError:
        messages = []

    # Ensure the initial message is always at the beginning, before any new messages are added
    if not messages or messages[0].get("content") != INITIAL_MESSAGE.get("content"):
        messages = [INITIAL_MESSAGE] + messages

    # Append the new message
    messages.append({"role": role, "content": content})

    # Maintain a rolling window of the last i messages, ensuring the initial message is included
    if len(messages) > 11:
        messages = [INITIAL_MESSAGE] + messages[-10:]

    with open(file_path, "w") as file:
        json.dump(messages, file, indent=4)


def read_json(file_path):
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return []


def groq_post_question():
    try:
        client = Groq(
            # api_key=os.environ.get("GROQ_API_KEY"),
            api_key=os.getenv("GROQ_API_KEY")
        )

        chat_completion = client.chat.completions.create(
            messages=read_json(MESSAGES_JSON),
            model="llama3-70b-8192",
        )

        reply = chat_completion.choices[0].message.content

        append_json(MESSAGES_JSON, "assistant", reply)
        return reply

    except Exception as e:
        error_message = f"An error occurred during GROQ post question: {e}"
        return error_message


def main():
    initialize_messages()

    print("Welcome to AI Chat. Type something to begin...")
    while True:
        user_input = input("")
        append_json(MESSAGES_JSON, "user", user_input)

        if user_input.lower() in ["exit", "quit"]:
            print("Exiting chat.")
            break
        response = groq_post_question()
        print(f"{YELLOW}{response}{RESET} \n")


if __name__ == "__main__":
    main()
