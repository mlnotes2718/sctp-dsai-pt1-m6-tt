# Study Notes: Customized LLM Telegram Bot Full Stack Deployment

## Goal

Using an LLM API (e.g., OpenAI, Gemini, Claude), we aim to build a customized LLM-powered application accessible via a Telegram bot as a frontend.

---

## Simplest Working Solution

* Telegram app built using **Python + Flask**
* LLM Service Call: **API** (e.g., `openai`, `google-genai`)
* Receiving Updates from Telegram via **webhook**
* Sending Message to Telegram via **requests**
* Deployed on **PaaS** [Render.com](https://render.com)

> This is the basic setup; we will iteratively enhance it through further testing and analysis.

---

## Frontend Choice - Why Use Telegram Bot

* Built using BotFather
* Native mobile experience
* No additional client app development required

---
## API Layer

### Receiving Updates from Telegram

#### Polling

* Server pulls new messages from Telegram bot regularly
* ✅ Easy setup
* ✅ Good for local development, testing, prototyping and proof-of-concept
* ❌ Inefficient for production (wastes compute)
* ❌ Requires periodic polling




#### Webhook

* Telegram pushes updates to server (HTTPS)
* ✅ Scalable and efficient
* ✅ Best for production use
* ❗ Requires public HTTPS URL (Render.com, ngrok for local testing)
* ❗ Requires additional code for multi-users if we include extra features like keeping chat history for context purpose

Please refer to the slides for more details:
https://docs.google.com/presentation/d/1Z9LkHiUPCFSz47OFb_9rxRdV4XgVZZzw0Ed7AC7hihM/edit?usp=sharing


### Sending Message to Telegram

* **Flask**: use synchronous `requests`
* **FastAPI**: natively supports `httpx` async calls

---

## Backend Technology Stack

### Programming Language

* **Python**: broad ecosystem, easy integration with AI libraries


### REST Framework Options

| **Criterion**            | **Flask**                                                     | **FastAPI**                                                                            |
| ------------------------ | ------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| **Concurrency model**    | WSGI (synchronous)                                            | ASGI (native `async`/`await`)                                                          |
| **Performance**          | Good for moderate load; single-threaded by default            | Excellent for high-throughput & I/O-bound workloads                                    |
| **Learning curve**       | Very gentle; ideal if you’ve used Flask before                | Slightly steeper (async paradigms & Pydantic), but well-documented                     |
| **Ideal for**            | Simple APIs, PoCs, monolithic apps, teams already Flask-savvy | Microservices, real-time features, high-concurrency, type-safe codebases               |

**When to pick Flask**
* Need a quick PoC or prototype and already know Flask.
* Can use for production if the traffic is low-to-medium and you don’t need heavy async I/O.

**When to pick FastAPI**
* Expect high concurrency and heavy async I/O.
* Need modern async features out of the box.


---

### Telegram Bot SDK

* Using `python-telegram-bot` handles all Telegram communication internally
* Supports both sync and async approaches
* Supports polling and webhook
* Eliminates manual `requests`/`httpx` handling
* Medium/High complexity
* For Telegram only deployment
* Not suitable for Telegram services that requires web interface



---
## LLM Service Call

* **REST API**

  * Vendor‑agnostic HTTP endpoints (GET/POST)
  * Swap providers by updating URLs with same function call
  * Suitable for web app that will be interfacing with multiple LLM services interchangeably
  * Suitable for new LLM service when their API is not available but the http endpoint has been established.

* **SDK**

  * Vendor‑specific libraries; e.g.:

    * `import openai`
    * `from google import genai`
  * Built‑in support for streaming, retries, function calls
---
## Possible Options

**Option 1: Flask Framework**
* Telegram app built using **Python + Flask**
* LLM Service Call: **API** (e.g., `openai`, `google-genai`)
* Receiving Updates from Telegram via **webhook**
* Sending Message to Telegram via **requests**
* Deployed on **PaaS** [Render.com](https://render.com)

**Option 2: FastAPI Framework**
* Telegram app built using **Python + FastAPI**
* LLM Service Call: **API** (e.g., `openai`, `google-genai`)
* Receiving Updates from Telegram via **webhook**
* Sending Message to Telegram via **httpx**
* Deployed on **PaaS** [Render.com](https://render.com)

**Option 3: Telegram Bot SDK**
* Telegram app built using **Python + Telegram-Bot-SDK** (`python-telegram-bot`)
* LLM Service Call: **API** (e.g., `openai`, `google-genai`)
* Receiving Updates from Telegram via **webhook**
* SDK supports sending message to Telegram e.g. `update.message.reply_text(response.output_text)`
* Deployed on **PaaS** [Render.com](https://render.com) using background worker (requires USD$7/mth subscription) or AWS Elastic Beanstalk

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
