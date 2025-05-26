# Study Notes: Customized LLM Telegram Bot Full Stack Deployment

## Goal

Using an LLM API (e.g., OpenAI, Gemini, Claude), we aim to build a customized LLM-powered application accessible via a Telegram bot as a frontend.

---

## Simplest Working Solution

* Web app built using **Python + Flask**
* LLM Service Call: **SDK** (e.g., `openai`, `google-genai`)
* Communication with front end via **webhook**
* Outbound HTTP calls made via **requests**
* Deployed on **PaaS** [Render.com](https://render.com)

> This is the basic setup; we will iteratively enhance it through further testing and analysis.

---

## Frontend - Telegram Bot

* Built using BotFather
* Native mobile experience
* No additional client app development required

---
## API Layer

### Receiving Updates from Telegram

#### Polling

* Backend regularly polls Telegram for new messages
* Easy to set up; ideal for prototyping
* Inefficient at scale and wastes compute
* Telegram client libraries map updates to user chats, so no extra user-differentiation logic needed

**Code snippet using REST API and polling**
```python
# Telegram API base URL
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# OpenAI REST endpoint
OPENAI_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_HEADERS = {
    "Authorization": f"Bearer {OPENAI_API_KEY}",
    "Content-Type": "application/json"
}

def fetch_updates(offset=None, timeout=30):
    params = {"timeout": timeout}
    if offset:
        params["offset"] = offset
    resp = requests.get(f"{TELEGRAM_API_URL}/getUpdates", params=params)
    resp.raise_for_status()
    return resp.json()["result"]

def send_message(chat_id, text):
    data = {"chat_id": chat_id, "text": text}
    resp = requests.post(f"{TELEGRAM_API_URL}/sendMessage", json=data)
    resp.raise_for_status()
    return resp.json()

def query_llm(user_text):
    payload = {
        "model": "gpt-4o",
        "messages": [{"role": "user", "content": user_text}]
    }
    resp = requests.post(OPENAI_URL, headers=OPENAI_HEADERS, json=payload)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]

def main():
    offset = None
    print("Bot started polling...")
    while True:
        try:
            updates = fetch_updates(offset=offset)
            for upd in updates:
                offset = upd["update_id"] + 1
                msg = upd.get("message")
                if not msg or "text" not in msg:
                    continue

                chat_id = msg["chat"]["id"]
                user_text = msg["text"]

                # Query LLM
                try:
                    reply = query_llm(user_text)
                except Exception as e:
                    reply = f"Error contacting LLM: {e}"

                # Send back to Telegram
                try:
                    send_message(chat_id, reply)
                except Exception as e:
                    print(f"Failed to send message: {e}")

        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(5)

        # A short sleep to avoid hitting Telegram rate limits
        time.sleep(1)

```

#### Webhook

* Telegram pushes updates over HTTPS to your server
* Efficient and scalable; best for production
* Requires public HTTPS endpoint (Render.com or via ngrok for local testing)

**Code snippet Using Webhook + Flask**
```python
app = Flask(__name__)

# Load credentials
TELEGRAM_TOKEN   = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY   = os.getenv("OPENAI_API_KEY")
openai.api_key   = OPENAI_API_KEY

# Telegram API base URL
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

@app.route(f"/webhook/{TELEGRAM_TOKEN}", methods=["POST"])
def telegram_webhook():
    payload = request.get_json(force=True)
    message = payload.get("message", {})

    # Only handle text messages
    if "text" in message:
        chat_id   = message["chat"]["id"]
        user_text = message["text"]

        # 1. Query OpenAI via SDK
        try:
            resp = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": user_text}]
            )
            reply = resp.choices[0].message.content
        except Exception as e:
            reply = f"❗️ OpenAI error: {e}"

        # 2. Send the reply back via Telegram REST
        try:
            requests.post(
                f"{TELEGRAM_API_URL}/sendMessage",
                json={"chat_id": chat_id, "text": reply}
            ).raise_for_status()
        except Exception as e:
            # Log sending errors server‐side; Telegram won't retry on webhook failure
            print(f"Failed to send message: {e}")

    return "", 200

```

### Sending Message to Telegram

* **requests**: synchronous HTTP calls
* **httpx**: asynchronous HTTP support
* **Flask**: use synchronous `requests` or wrap `httpx` with ASGI tooling
* **FastAPI**: natively supports `httpx` async calls

---

## Backend Technology Stack

### Programming Language

* **Python**: broad ecosystem, easy integration with AI libraries


### REST Framework Options

| Framework | Async | Throughput       | Complexity | Use Case                    | When to Choose                                              |
| --------- | ----- | ---------------- | ---------- | --------------------------- | ----------------------------------------------------------- |
| Flask     | No    | Lower under load | Low        | Prototyping, internal tools | Light traffic; minimal dependencies; quick proof-of-concept |
| FastAPI   | Yes   | High concurrency | Moderate   | Public APIs, microservices  | High request rates; async I/O; auto-generated OpenAPI docs  |

#### Framework Nuances

* **Flask + Async**: Flask isn’t natively async—if you use `httpx` in async mode, you’ll need an ASGI wrapper (e.g., `asgiref`) or switch to FastAPI/Quart.
* **FastAPI Advantages**: Built on Starlette, fully async; uses Pydantic for validation; automatic docs; ideal for high-throughput webhook and LLM streaming scenarios.

```python
# ——— FastAPI app ——————————————————————————————————————
app = FastAPI()

# — Health check / root endpoint —
@app.get("/")
async def health_check():
    return {"status": "alive"}

@app.on_event("startup")
async def startup_event():
    # create and store shared HTTPX client with a 10s timeout
    app.state.http = AsyncClient(timeout=10.0)

    # AsyncOpenAI client
    app.state.openai = AsyncOpenAI(api_key=OPENAI_API_KEY)

    # 1. Delete existing webhook & drop pending updates
    try:
        resp = await app.state.http.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/deleteWebhook",
            json={"drop_pending_updates": True}
        )
        resp.raise_for_status()
        data = resp.json()
        if not data.get("ok"):
            logger.error("deleteWebhook failed: %s", data)
    except HTTPError as e:
        logger.error("Error deleting Telegram webhook", exc_info=True)

    # 2. Register new webhook
    hook_endpoint = f"{WEBHOOK_URL}/webhook/{TELEGRAM_TOKEN}"
    try:
        resp = await app.state.http.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook",
            json={"url": hook_endpoint}
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("ok"):
            logger.info("Registered webhook at %s", hook_endpoint)
        else:
            logger.error("setWebhook failed: %s", data)
    except HTTPError:
        logger.error("Error setting Telegram webhook", exc_info=True)


@app.post("/webhook/{token}")
async def telegram_webhook(token: str, request: Request):
    # validate token
    if token != TELEGRAM_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid token")

    body = await request.json()

    # support both new and edited messages
    msg = body.get("message") or body.get("edited_message")
    if not msg:
        return {"ok": True}

    text = msg.get("text")
    if not text:
        # ignore stickers, photos, etc.
        return {"ok": True}

    chat_id = msg["chat"]["id"]

    # — Query OpenAI —
    try:
        completion = await app.state.openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": text}],
            timeout=10.0  # override if needed
        )
        reply = completion.choices[0].message.content
    except Exception:
        logger.exception("OpenAI API error")
        reply = "❗️ Sorry, something went wrong on the AI side. Please try again."

    # — Send reply back to Telegram —
    try:
        resp = await app.state.http.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": reply}
        )
        resp.raise_for_status()
    except HTTPError:
        logger.error("Failed to send Telegram message", exc_info=True)

    return {"ok": True}


@app.on_event("shutdown")
async def shutdown_event():
    # close HTTPX client
    await app.state.http.aclose()
    # close OpenAI client (if it supports aclose)
    try:
        await app.state.openai.aclose()
    except AttributeError:
        pass



```

---

### Telegram Bot SDK

* Using `python-telegram-bot` handles all Telegram communication internally
* Supports both sync and async approaches
* Eliminates manual `requests`/`httpx` handling
* Medium/High complexity
* For Telegram only deployment

#### Telegram-Bot Library Best Practices

* **Version v20+** is asyncio-driven—pair with FastAPI (or an ASGI wrapper) for best performance.
* Use `bot.delete_webhook(drop_pending_updates=True)` on startup to clear old updates, then `bot.set_webhook(url=WEBHOOK_URL)`.
* Check webhook status via `bot.get_webhook_info()` in a status endpoint (e.g., `@app.route('/status')`).
* Organize handlers in separate modules and use conversation handlers for multi-step interactions.
* Store `BOT_TOKEN` and LLM API keys in environment variables or a secrets manager; never commit them to source.

**Code snippet using Telegram Bot SDK**
```Python
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

.....

# Initialize the OpenAI Responses API client
openai_client = OpenAI(api_key=OPENAI_API_KEY)  # :contentReference[oaicite:0]{index=0}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text("👋 Hello! I'm your AI assistant.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        user_text = update.message.text

        # Call the Responses API with a simple instruction
        response = openai_client.responses.create(
            model="gpt-4o",
            instructions="You are a helpful assistant.",
            input=user_text,
        )
        await update.message.reply_text(response.output_text)

def main():
    # Build the bot application
    app = ApplicationBuilder().token(TOKEN).build()

    # Register handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start the webhook listener, dropping any pending updates on startup
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{TOKEN}",
        drop_pending_updates=True,  
    )
```


---
## LLM Communication

* **REST API**

  * Vendor‑agnostic HTTP endpoints (GET/POST)
  * Swap providers by updating URLs
  * Suitable for web app that will be interfacing with multiple LLM services

* **SDK**

  * Vendor‑specific libraries; e.g.:

    * `import openai`
    * `from google import genai`
  * Built‑in support for streaming, retries, function calls
---

# Backend Deployment Options

1. **Virtual Machine (VM)**

   * **Setup**: Spin up a VM on GCP/Azure/AWS
   * **Pros**: Maximum control; low ongoing cost
   * **Cons**: High initial setup; manual scaling; heavy ops overhead; need to manage the web server

2. **Platform as a Service (PaaS)**

   * **Examples**: Render, Heroku, Railway
   * **Pros**: Fast deploy; built-in autoscaling; minimal ops
   * **Cons**: Higher per-use cost; limited low-level control

3. **Managed Service**

   * **Examples**: AWS Elastic Beanstalk, Google App Engine
   * **Pros**: Granular resource control; managed scaling
   * **Cons**: Medium ops overhead; vendor lock-in risk

### Deployment Comparison

| Option          | Cost                        | Scalability                 | Ops Overhead |
| --------------- | --------------------------- | --------------------------- | ------------ |
| VM              | Low long-term, high upfront | High (manual scaling)       | High         |
| PaaS            | Medium, pay-per-use         | Good (auto-scaling)         | Low          |
| Managed Service | Medium–High                 | Very good (managed scaling) | Medium       |

---

*End of Notes*
