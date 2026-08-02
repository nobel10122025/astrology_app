# Backend - Flask Application

This is the backend Flask application for Subathuvam Pavathuvam.

## Getting Started

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. Create a virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Running the Application

Start the Flask development server:
```bash
python app.py
```

The API will be available at [http://localhost:5000](http://localhost:5000)

### API Endpoints

- `GET /` - Home endpoint with welcome message
- `GET /api/health` - Health check endpoint

### Running in Production

For production, use a WSGI server like Gunicorn:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Configuration (environment variables)

Copy `.env.example` to `.env` for local dev, or set these in your host's
dashboard (e.g. Render) for deployment. See `.env.example` for the full list.

Key variables:

- `GROQ_API_KEY` — Groq key for the LLM judge, narrator and tool planner.
- `LLM_PROVIDER` — `groq` (default), `anthropic`, or `ollama` for narration.

#### Routing LLM calls through Portkey (optional)

Set `PORTKEY_API_KEY` and every Groq call (judge, narrator, planner) is routed
through the [Portkey](https://portkey.ai) AI gateway — no code change, no extra
dependency — giving observability, caching, retries and fallbacks. Leave it
unset to call Groq directly (the default). Choose one way for Portkey to reach
Groq:

- **Virtual key:** set `PORTKEY_VIRTUAL_KEY` (Portkey stores the Groq key, so
  `GROQ_API_KEY` isn't needed by this service).
- **Pass-through:** set `PORTKEY_PROVIDER=groq` (default) and `GROQ_API_KEY` is
  forwarded to Groq.

Optionally set `PORTKEY_CONFIG` to a saved Portkey config id for
dashboard-defined routing/fallback/cache rules.
