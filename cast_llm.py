import os
import json
import argparse

import openai

from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from dotenv import load_dotenv

load_dotenv()

CHATGPT_3_5_TURBO = "gpt-3.5-turbo"
DEFAULT_MODEL = CHATGPT_3_5_TURBO

# Initialize OpenAI GPT API (replace 'your-openai-api-key' with your actual key)
__OPEN_AI_API_KEY = os.getenv("CASTLLM_OPENAI_KEY", None)
if not __OPEN_AI_API_KEY:
    print("Please set the CASTLLM_OPENAI_KEY environment variable or in the .env file.")
    exit(1)

openai.api_key = __OPEN_AI_API_KEY

# Initialize rich console
console = Console()


# Function to call the ChatGPT API
def chat_with_gpt(messages, model=DEFAULT_MODEL):
    model_engine = model if model else DEFAULT_MODEL
    return openai.ChatCompletion.create(model=model_engine, messages=messages)


# Function to save the session
def save_session(filename, messages, model, topic):
    session_data = {"model": model, "topic": topic, "messages": messages}
    with open(filename, "w") as f:
        json.dump(session_data, f)


# Function to display topic in a fancy way
def load_session(session_file):
    with open(session_file, "r") as f:
        session_data = json.load(f)
        messages = session_data["messages"]
        model = session_data.get("model", DEFAULT_MODEL)
        topic = session_data.get("topic", None)
    return messages, model, topic


def display_topic(topic):
    console.print(
        Panel(
            f"[bold cyan]Chat Topic: {topic}[/bold cyan]",
            expand=False,
            border_style="green",
        )
    )


# Main function


def cli_display_messages(messages, topic):
    if topic:
        display_topic(topic)

    for msg in messages:
        role, content = msg["role"], msg["content"]
        console.print(f"[green]{role}[/green]: {content}")


def main(args):
    session_file = args.load_session
    model = args.use
    messages = []
    topic = None

    # Load previous session if any
    if session_file:
        messages, model, topic = load_session(session_file)

    # Display old messages and topic
    cli_display_messages(messages, topic)

    # No messages? Start a new session
    if not messages:
        messages.append(
            {"role": "system", "content": "You are now chatting with ChatGPT."}
        )

    try:
        while True:
            # User message
            user_message = input("You: ")

            messages.append({"role": "user", "content": user_message})

            # Chat with GPT-3
            response = chat_with_gpt(messages, model)
            gpt_message = response["choices"][0]["message"]["content"]
            messages.append({"role": "assistant", "content": gpt_message})

            # Display GPT-3's message
            console.print(f"[red]ChatGPT[/red]: {gpt_message}")

            # Save session
            if len(messages) >= 3:
                # Generate filename
                if not session_file:
                    # Make a call to GPT-3 for generating a summary
                    summary_request = [
                        {
                            "role": "system",
                            "content": "You are now chatting with ChatGPT.",
                        },
                        messages[1],
                        messages[2],
                        {
                            "role": "user",
                            "content": "Summarize our conversation in 1 to 5 words.",
                        },
                    ]
                    # Always summarize with the CHATGPT_3_5_TURBO model
                    summary_response = chat_with_gpt(
                        summary_request, model=CHATGPT_3_5_TURBO
                    )
                    summary_text = summary_response["choices"][0]["message"][
                        "content"
                    ].strip()

                    # Display the chat topic in a fancy way
                    topic = summary_text
                    display_topic(topic)

                    dt_str = datetime.now().strftime("%Y%m%d-%H%M%S")
                    session_file = f"sessions/{summary_text.replace(' ', '_').replace('.', '').replace(',', '')}-{dt_str}.json"

                    if not os.path.exists("sessions"):
                        os.mkdir("sessions")

                save_session(session_file, messages, model, topic)

    except KeyboardInterrupt:
        print("\nExiting. Session saved.")
        exit(0)


# Entry point
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chat with GPT-3 or GPT-4.")
    parser.add_argument(
        "--load-session", type=str, help="Load a previous chat session from a file."
    )
    parser.add_argument(
        "--use",
        type=str,
        help="Specify which GPT model to use. (gpt-3.5-turbo or gpt-4 to start)",
        default=DEFAULT_MODEL,
    )
    args = parser.parse_args()

    main(args)
