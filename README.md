# CrowdFund Egypt 🇪🇬

A modern, full-stack crowdfunding web platform developed with **Django 6**, **Bootstrap 5**, and **Generative AI** enabling creators, innovators, and charitable organizations across Egypt to launch campaigns, raise funds, and connect with supporters.

---

## 🌟 Generative AI Assistant: "Masry Fund AI"

CrowdFund Egypt includes a smart **Generative AI Assistant** that operates with **live project and platform context**, providing real-time campaign recommendations, donation guidance, and answering user queries regarding platform policies and active Egyptian initiatives.

```
┌─────────────────────────────────────────────────────────────┐
│                      Client Browser                         │
│   (Floating AI Chat Widget with Starter Chips & Markdown)   │
└──────────────────────────────┬──────────────────────────────┘
                               │ POST /api/chat/ (JSON payload + History)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                   Django Backend Endpoint                   │
│                    (apps/core/views.py)                     │
└──────────────────────────────┬──────────────────────────────┘
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
    ┌────────────────────┐          ┌────────────────────┐
    │  Django ORM Query  │          │   AI Service       │
    │  (Live Campaigns,  │          │ (apps/core/        │
    │   Categories,      │ ───────► │  services/         │
    │   Funding Targets, │          │  ai_service.py)    │
    │   Rules, Stats)    │          └─────────┬──────────┘
    └────────────────────┘                    │
                                              ▼
                                    ┌────────────────────┐
                                    │ Google Gemini API  │
                                    │ (gemini-2.5-flash) │
                                    │ (Free-Tier REST)   │
                                    └─────────┬──────────┘
                                              │ AI Response
                                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Frontend Dynamic Chat UI Display               │
│         (Markdown links to campaigns, bold, stats)          │
└─────────────────────────────────────────────────────────────┘
```

---

## 🤖 AI Provider & Model

- **Provider**: **Google Gemini API** (Google AI Studio)
- **Model**: `gemini-2.5-flash` / `gemini-1.5-flash`
- **Why Selected**:
  - 100% Free API access without credit card required.
  - High performance & low latency for conversational chat.
  - Generous free-tier quota (up to 15 Requests Per Minute).
  - Lightweight REST integration via Python `requests` (no heavy extra frameworks needed).
  - Also supports **Groq** (`llama-3.3-70b-versatile`) as an alternate provider.
  - Features a built-in **Smart Offline Fallback Engine** so the platform works seamlessly even if offline or before an API key is supplied.

---

## 🚀 Getting Started & Configuration

### 1. Prerequisites
- Python 3.10+ (tested with Python 3.12 / 3.14)
- Pip

### 2. Environment Variables (.env)
Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Get your **FREE** Gemini API key in 1 minute from [Google AI Studio](https://aistudio.google.com/app/apikey) and add it to `.env`:

```env
SECRET_KEY=your_secret_key_here
DEBUG=True

GEMINI_API_KEY=your_free_gemini_api_key_here
AI_PROVIDER=gemini
AI_MODEL=gemini-2.5-flash
```

### 3. Run Migrations & Seed Data (Optional)
```bash
python manage.py migrate
python manage.py seed_data
```

### 4. Start the Development Server
```bash
python manage.py runserver
```
or double-click `run.bat` on Windows.

Visit: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

---

## 📡 API Documentation

### **Chat Endpoint**
- **URL**: `/api/chat/`
- **Method**: `POST`
- **Content-Type**: `application/json`

#### **Request Body:**
```json
{
  "message": "Can you recommend environmental or solar energy campaigns in Egypt?",
  "history": [
    {
      "role": "user",
      "content": "Hello!"
    },
    {
      "role": "assistant",
      "content": "Marhaban! How can I assist you with CrowdFund Egypt campaigns today?"
    }
  ]
}
```

#### **Response Body (200 OK):**
```json
{
  "status": "success",
  "response": "Here are active environmental campaigns on CrowdFund Egypt:\n\n• **[Solar Powered Water Pumps for Rural Upper Egypt](/projects/solar-powered-water-pumps-for-rural-upper-egypt/)**\n  - Target: 350,000 EGP | Raised: 210,000 EGP (60.0% funded)\n  - Provides sustainable solar pumping for agricultural communities in Upper Egypt."
}
```

---

## 🧪 Testing Prompts for Demonstration

Try these 5 prompts to demonstrate that the AI assistant is directly hooked to live platform data:

1. **Campaign Discovery**:
   > *"Can you recommend solar or clean energy projects currently raising funds?"*
   > → Recommends the Upper Egypt Solar Pumps campaign with exact target and raised percentage.

2. **Healthcare Exploration**:
   > *"What hospital or medical projects can I donate to?"*
   > → Highlights the Children's Hospital Emergency Unit renovation campaign.

3. **Multi-Turn Context**:
   > **User**: *"Tell me about the robotics hub campaign."*
   > **AI**: *Gives details on the Cairo Youth Robotics & AI Hub.*
   > **User**: *"How much money has it raised so far?"*
   > → AI maintains memory and extracts the specific donation total (95,000 EGP).

4. **Platform Rules & Policy**:
   > *"Under what conditions can a campaign creator cancel their project?"*
   > → Explains the platform policy: cancellation is permitted only if donations are less than 25% of the target.

5. **Campaign Launch Advice**:
   > *"How do I start a new campaign on this website?"*
   > → Step-by-step guidance linking to `/projects/create/`.

---

## 🎤 Instructor Presentation Pitch

> *"We integrated a project-aware Generative AI Chatbot ('Masry Fund AI') into CrowdFund Egypt using Google's free-tier Gemini API. Rather than being an isolated demo or generic bot, our backend dynamically extracts real-time platform data—including active campaigns, funding percentages in EGP, category structures, and cancellation rules (<25% threshold)—and feeds this structured context to the LLM. The AI delivers factual recommendations with direct campaign links, multi-turn conversation memory, and answers questions in both English and Arabic. If an external API key is not configured, a built-in smart fallback engine handles user requests seamlessly."*

---

## 🛡️ Security & Quality
- API keys are strictly managed via `.env` and `os.environ` (never exposed in client code).
- CSRF protection enabled on all API requests.
- Input validation and sanitized Markdown rendering prevent XSS vulnerabilities.
- Multi-tier error handling (rate limit 429, timeouts, network interruptions).
