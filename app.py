# app.py

# This is a simple Flask application that serves as a web interface for a financial chatbot using the Google Gemini API.
# The application allows users to ask finance-related questions and receive answers from the chatbot.
# It also includes a Telegram bot that can respond to user queries via Telegram.
# The application uses SQLite to store user data and logs.
# The application is designed to be run locally and can be deployed to a cloud service like Google Cloud Run.
# The application uses the Flask framework for web development and the Google Gemini API for generating responses.
# The application is structured with multiple routes to handle different functionalities.
# The application uses the dotenv library to load environment variables from a .env file for local development.
# The application uses the requests library to make HTTP requests to the Telegram API for sending messages.
# The application uses the markdown library to convert text to HTML for rendering in the web interface.
# The application uses the datetime library to handle timestamps for user logs.
# The application is designed to be user-friendly and provides a simple interface for users to interact with the chatbot.

# Import necessary libraries
# Flask is a micro web framework for Python
# requests is a library for making HTTP requests
# google.genai is a library for interacting with the Google Gemini API
# sqlite3 is a library for interacting with SQLite databases
# datetime is a library for handling dates and times
# markdown and markdown2 are libraries for converting Markdown text to HTML
# os is a library for interacting with the operating system
# dotenv is a library for loading environment variables from a .env file
from flask import Flask, render_template, request
import requests
from google import genai
import sqlite3
import datetime
from datetime import timezone, datetime
import markdown, markdown2
import os

# Load environment variables from .env file
# The following is for local development
# Uncomment the following lines if you want to load environment variables from a .env file
# dotenv is a library for loading environment variables from a .env file
# from dotenv import load_dotenv
# load_dotenv()


### Load environment variables
genmini_api_key = os.getenv('GEMINI_API_KEY')
# The following is for the telegram bot
# The telegram bot token is used to authenticate the bot with the Telegram API
gemini_telegram_token = os.getenv('GEMINI_TELEGRAM_TOKEN')

### Initialize the Google Gemini client
genmini_client = genai.Client(api_key=genmini_api_key)
genmini_model = "gemini-2.0-flash"

### --------- Flask application setup ---------
# The Flask application is created using the Flask class
app = Flask(__name__)

### Index page and app routes setup
@app.route("/",methods=["GET","POST"])
def index():
        return(render_template("index.html"))


### Main landing page and app routes setup
@app.route("/main",methods=["GET","POST"])
def main():
    name = request.form.get("name")
    if name == "":
        return(render_template("index.html"))
    else:
        print(name)
        t = datetime.now(timezone.utc)
        conn = sqlite3.connect(r'user.db')
        c = conn.cursor()
        c.execute('INSERT INTO user (name,timestamp) VALUES(?,?)',(name,t))
        conn.commit()
        c.close()
        conn.close()
        return(render_template("main.html"))


# Return to the index page
@app.route("/checkout",methods=["GET","POST"])
def checkout():
    return(render_template("index.html"))

# The following route is setup for the logs pages to return to the main page without data processing
@app.route("/home",methods=["GET","POST"])
def home():
    return(render_template("main.html"))

### ----------- Gemini Chatbot Routes -----------
### The following route is displayed when the user clicks on the Gemini button
@app.route("/gemini",methods=["GET","POST"])
def gemini():
    name = request.form.get("name")
    return(render_template("gemini.html",name=name))

### The following route is for the Gemini chatbot
@app.route("/gemini_reply",methods=["GET","POST"])
def gemini_reply():
    # Getting the user query from the form
    q = request.form.get("q")

    # System prompt for financial questions
    system_prompt = """ 
    You are a financial expert.  Answer ONLY questions related to finance, economics, investing, 
    and financial markets. If the question is not related to finance, 
    state that you cannot answer it."""

    # Construct the prompt with system prompt and user query
    prompt = f"{system_prompt}\n\nUser Query: {q}"

    q = request.form.get("q")
    r = genmini_client.models.generate_content(
        model=genmini_model,
        contents=prompt
    )
    r_html = markdown.markdown(
            r.text if r.text is not None else "",
            extensions=["fenced_code", "codehilite"]  
    )
    return(render_template("gemini_reply.html",r=r_html))



### The following route is for the logs page
@app.route("/logs",methods=["GET","POST"])
def logs():
    conn = sqlite3.connect(r'user.db')
    c = conn.cursor()
    c.execute("SELECT * FROM user ORDER BY timestamp")
    r="\n"
    for row in c:
        r = r + str(row) + '\n'
        print(row)
    c.close()
    conn.close()
    return(render_template("logs.html",r=r))

@app.route("/del_logs",methods=["GET","POST"])
def del_logs():
    conn = sqlite3.connect(r'user.db')
    c = conn.cursor()
    c.execute("delete from user")
    conn.commit()
    c.close()
    conn.close()
    return(render_template("del_logs.html"))


### The following route is for the telegram bot
@app.route("/telegram_page",methods=["GET","POST"])
def telegram_page():
    domain_url = os.getenv('WEBHOOK_URL')
    webhook_url = f"https://api.telegram.org/bot{gemini_telegram_token}/deleteWebhook"
    requests.post(webhook_url, json={"url": domain_url, "drop_pending_updates": True})
    status = "The telegram bot is not running. Click the button below to start it."
    return(render_template("telegram.html", status=status))

@app.route("/start_telegram",methods=["GET","POST"])
def start_telegram():
    domain_url = os.getenv('WEBHOOK_URL')
    webhook_url = f"https://api.telegram.org/bot{gemini_telegram_token}/setWebhook?url={domain_url}/telegram"
    # Set the webhook URL for the Telegram bot
    webhook_response = requests.post(webhook_url, json={"url": domain_url, "drop_pending_updates": True})
    print('webhook:', webhook_response)
    if webhook_response.status_code == 200:
        # set status message
        status = "The telegram bot is running. Please check with the telegram bot. @gemini_tt_bot"
    else:
        status = "Failed to start the telegram bot. Please check the logs."
    
    return(render_template("telegram.html", status=status))


@app.route("/stop_telegram",methods=["GET","POST"])
def stop_telegram():
    # Remove the webhook URL for the Telegram bot
    webhook_url = f"https://api.telegram.org/bot{gemini_telegram_token}/deleteWebhook"
    remove_webhook_response = requests.post(webhook_url)
    print(remove_webhook_response)
    if remove_webhook_response.status_code == 200:
        status = "The telegram bot is stopped."
    else:
        status = "Unable to stop telegram.Please check the logs."


    return(render_template("telegram.html", status=status))

@app.route("/telegram",methods=["GET","POST"])
def telegram():
    update = request.get_json()
    if "message" in update and "text" in update["message"]:
        # Extract the chat ID and message text from the update
        chat_id = update["message"]["chat"]["id"]
        text = update["message"]["text"]

        if text == "/start":
            r_text = "Welcome to the Gemini Telegram Bot! You can ask me any finance-related questions."
        else:
            # Process the message and generate a response
            system_prompt = "You are a financial expert.  Answer ONLY questions related to finance, economics, investing, and financial markets. If the question is not related to finance, state that you cannot answer it."
            prompt = f"{system_prompt}\n\nUser Query: {text}"
            r = genmini_client.models.generate_content(
                model=genmini_model,
                contents=prompt
            )
            r_text = r.text
            # Convert the response to HTML
            r_html = markdown.markdown(
                r_text if r_text is not None else "",
                extensions=["fenced_code", "codehilite"]
            )
        
        # Send the response back to the user
        send_message_url = f"https://api.telegram.org/bot{gemini_telegram_token}/sendMessage"
        requests.post(send_message_url, data={"chat_id": chat_id, "text": r_html})
    # Return a 200 OK response to Telegram
    # This is important to acknowledge the receipt of the message
    # and prevent Telegram from resending the message
    # if the server doesn't respond in time
    return('ok', 200)

### The following route is for the payment page
@app.route("/paynow",methods=["GET","POST"])
def paynow():

    return(render_template("paynow.html"))

if __name__ == "__main__":
    app.run()
