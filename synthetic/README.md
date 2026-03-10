# MH-OAN Synthetic Conversation Pipeline

Generate and view synthetic farmer-agent conversations for MahaVistaar.

## Prerequisites

- Python 3.11+
- Node.js 18+ (for the viewer frontend)
- Access to Marqo search endpoint (for real document/video search)
- Mapbox API token (for real geocoding)
- OpenAI API key (for LLM)

## Setup

### 1. Environment variables

Create a `.env` file in the project root (`mh-oan-api/.env`) with:

```bash
# LLM
OPENAI_API_KEY=sk-...
LLM_PROVIDER=openai
LLM_AGRINET_MODEL_NAME=gpt-5.2
LLM_MODERATION_MODEL_NAME=gpt-4.1-mini

# Search (Marqo)
MARQO_ENDPOINT_URL=http://10.10.85.88:8882/
MARQO_INDEX_NAME=sunbird-va-index

# Geocoding (Mapbox)
MAPBOX_API_TOKEN=pk.eyJ1...

# Optional
LOGFIRE_TOKEN=pylf_v1_...
ENABLE_INSTRUMENTATION=true
```

### 2. Python virtual environment

```bash
cd mh-oan-api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Install frontend dependencies

```bash
cd viewer
npm install
```

## Running

### Start the backend API

```bash
# From project root (mh-oan-api/)
.venv/bin/uvicorn synthetic.server:app --port 8000 --reload
```

The backend runs on `http://localhost:8000`. Key endpoints:

| Endpoint | Method | Description |
|---|---|---|
| `/api/simulate` | POST | Run a new conversation (SSE stream) |
| `/api/files` | GET | List saved conversation files |
| `/api/conversations` | GET | List all conversation summaries |
| `/api/conversation/{id}` | GET | Get a full conversation |
| `/api/conversation/{id}` | DELETE | Delete a conversation |

### Start the frontend viewer

```bash
# From viewer/ directory
cd viewer
npm run dev
```

The frontend runs on `http://localhost:3000`.

### Both at once (two terminals)

**Terminal 1 — Backend:**
```bash
cd mh-oan-api
.venv/bin/uvicorn synthetic.server:app --port 8000 --reload
```

**Terminal 2 — Frontend:**
```bash
cd mh-oan-api/viewer
npm run dev
```

Open `http://localhost:3000` in your browser.

## Simulate API

POST `/api/simulate` with JSON body:

```json
{
  "max_turns": 25,
  "language": "mr",
  "target_language": "mr",
  "scenario_id": "crop_pest",
  "force_language_switch": false
}
```

All fields are optional. The API streams SSE events:

- `env` — session environment (session ID, date, target language)
- `profile` — generated farmer profile
- `user_message` — farmer message each turn
- `agent_message` — agent response with tool calls
- `language_switch` — when target language changes mid-conversation
- `done` — conversation record saved
- `error` — if something goes wrong

## Project structure

```
synthetic/
├── server.py          # FastAPI backend (viewer API + simulate endpoint)
├── generate.py        # Conversation generation logic
├── agrinet.py         # MahaVistaar agent (pydantic-ai)
├── moderation.py      # Content moderation agent
├── mock_data.py       # Mock data for weather, mandi, services, etc.
├── models.py          # LLM model configuration
├── deps.py            # FarmerContext dependencies
├── test_prompts.py    # Prompt quality test suite
├── tools/             # All tools (real + mock)
│   ├── __init__.py    # TOOLS list
│   ├── common.py      # reasoning_tool, planning_tool
│   ├── search.py      # Real Marqo search (documents + videos)
│   ├── maps.py        # Real Mapbox geocoding
│   ├── terms.py       # Real glossary term search
│   ├── scheme_info.py # Scheme codes + fixture info
│   ├── weather.py     # Mock weather
│   ├── mandi.py       # Mock mandi prices
│   ├── agri_services.py  # Mock agricultural services
│   ├── agristack.py   # Mock agristack data
│   ├── mahadbt.py     # Mock MahaDBT status
│   └── staff_contact.py  # Mock staff contact
└── user/              # Synthetic farmer agent
    ├── agent.py       # Farmer user agent
    ├── profile.py     # FarmerProfile generation
    └── tools.py       # EndConversation tool

viewer/                # Next.js frontend for viewing conversations
```

## Testing prompts

```bash
# Run all languages
.venv/bin/python -m synthetic.test_prompts --verbose

# Run specific language
.venv/bin/python -m synthetic.test_prompts --lang mr --verbose
```

## Generated data

Conversations are saved to `data/synthetic/` as JSONL files, one file per session.
