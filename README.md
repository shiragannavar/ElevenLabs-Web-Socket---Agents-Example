# ElevenLabs Agent Voice Chat

A beautiful, natural voice conversation interface for ElevenLabs AI agents using WebSockets.

## Features

- 🎙️ **Natural Conversations**: Speak naturally without manual mute/unmute
- 🎨 **Beautiful Centered UI**: Modern, intuitive interface
- 🔊 **Real-time Audio**: Low-latency voice streaming with intelligent queueing
- 📝 **Live Transcripts**: See conversation history in real-time
- 🎯 **Simple Setup**: Configure once, use anytime
- 🔒 **Secure**: Credentials stored in config file, not in UI

## Prerequisites

- Python 3.7 or higher
- A modern web browser (Chrome, Firefox, Safari, or Edge)
- ElevenLabs account with an agent created
- Microphone access

## Setup

1. **Configure your credentials**:

Open `config.env` and add your ElevenLabs credentials:

```env
AGENT_ID=agent_4201k9q7057vfz3bam4bew8vph9n
API_KEY=your_actual_api_key_here
```

Replace `your_actual_api_key_here` with your real ElevenLabs API key.

2. **Install dependencies** (if not already installed):
```bash
source venv/bin/activate
pip install -r requirements.txt
```

## Running the Application

1. **Start the server**:
```bash
source venv/bin/activate
python app.py
```

2. **Open your browser** and navigate to:
```
http://localhost:5001
```

3. **Click "Start Conversation"** and start speaking!

That's it! No need to enter credentials in the UI.

## How It Works

1. **Backend (app.py)**: Flask server that proxies WebSocket connections between your browser and ElevenLabs API
2. **Frontend (templates/index.html)**: Web interface that:
   - Captures audio from your microphone
   - Sends audio chunks to the agent via WebSocket
   - Receives and plays audio responses
   - Displays conversation transcripts

## Audio Format

- **Input**: PCM 16-bit, 16kHz mono audio from your microphone
- **Output**: Audio received from ElevenLabs agent (format depends on agent configuration)

## Troubleshooting

### Microphone not working
- Make sure you grant microphone permissions when prompted
- Check your browser's site settings for microphone access

### Connection fails
- Verify your Agent ID and API Key are correct
- Check your internet connection
- Ensure the Flask server is running

### No audio output
- Check your system volume
- Try a different browser
- Ensure your audio output device is working

### Server won't start
- Make sure port 5001 is not in use: `lsof -i :5001`
- Activate the virtual environment: `source venv/bin/activate`
- Reinstall dependencies: `pip install -r requirements.txt`

## Call flow: start to end

There are **two** WebSocket hops:

1. **Browser ↔ Local server** — `ws://localhost:5001/ws` (this app)
2. **Local server ↔ ElevenLabs** — `wss://api.elevenlabs.io/v1/convai/conversation?agent_id=...` (with `xi-api-key` header)

The sections below follow **one full call** from clicking **Start Conversation** through **End Conversation**.

---

### Phase 1 — Browser connects to this app

| Step | Who | What happens |
|------|-----|----------------|
| 1 | Browser | Opens `WebSocket` to `/ws` |
| 2 | Browser → App | First message after `onopen` |

**Example — client ready (browser → app):**

```json
{
  "action": "connect"
}
```

| 3 | App | Reads `AGENT_ID` and `API_KEY` from `config.env`, connects upstream to ElevenLabs |
| 4 | App → Browser | Synthetic status so the UI can start mic + audio |

**Example — connected (app → browser):**

```json
{
  "status": "connected"
}
```

If credentials are missing, the app sends instead:

```json
{
  "error": "Server not configured. Please set credentials in config.env file."
}
```

---

### Phase 2 — Conversation initiation (ElevenLabs → browser)

After the upstream WebSocket is live, ElevenLabs sends metadata. This app **forwards the JSON as-is** to the browser.

**Example — initiation metadata (server → client):**

```json
{
  "type": "conversation_initiation_metadata",
  "conversation_initiation_metadata_event": {
    "conversation_id": "conv_01abc...",
    "agent_output_audio_format": "pcm_16000",
    "user_input_audio_format": "pcm_16000"
  }
}
```

The UI uses `agent_output_audio_format` to decode playback (e.g. PCM sample rate or encoded format).

---

### Phase 3 — Client tells the agent session is configured (browser → ElevenLabs, via proxy)

The frontend sends ElevenLabs **publish** payloads. The proxy forwards the **string** unchanged.

**Example — optional overrides (browser → ElevenLabs):**

```json
{
  "type": "conversation_initiation_client_data",
  "conversation_config_override": {},
  "dynamic_variables": {}
}
```

(Omit empty fields if you do not need overrides; the minimal shape is `{ "type": "conversation_initiation_client_data" }`.)

---

### Phase 4 — Continuous microphone upload (browser → ElevenLabs)

While the user speaks, the UI streams **base64-encoded PCM** chunks (from the mic).

**Example — user audio chunk (browser → ElevenLabs):**

```json
{
  "user_audio_chunk": "Base64EncodedPcm16BitMono..."
}
```

Notes:

- Chunks are sent **repeatedly** while the conversation is active (not one blob per utterance).
- Format aligns with `user_input_audio_format` from initiation metadata (commonly 16 kHz PCM in this app).

---

### Phase 5 — Server events during the conversation (ElevenLabs → browser)

These arrive **in any order** depending on speech, model, and agent settings. All are JSON with a top-level `type`.

#### Ping / keep-alive

**Example — ping (server → client):**

```json
{
  "type": "ping",
  "ping_event": {
    "event_id": 42,
    "ping_ms": 25
  }
}
```

**Example — pong reply (client → server):**

```json
{
  "type": "pong",
  "event_id": 42
}
```

#### User speech as text

**Example — user transcript (server → client):**

```json
{
  "type": "user_transcript",
  "user_transcription_event": {
    "user_transcript": "What is the weather like today?"
  }
}
```

#### Agent text (before or alongside TTS)

**Example — agent response (server → client):**

```json
{
  "type": "agent_response",
  "agent_response_event": {
    "agent_response": "I can help you check the weather for your location."
  }
}
```

#### Agent voice (streamed)

**Example — audio chunk (server → client):**

```json
{
  "type": "audio",
  "audio_event": {
    "audio_base_64": "Base64EncodedAgentAudio...",
    "event_id": 7
  }
}
```

Many `audio` messages may arrive for a single spoken reply; the UI **queues** them so playback does not overlap.

#### Interruption and corrections (optional)

**Example — interruption (server → client):**

```json
{
  "type": "interruption",
  "interruption_event": {
    "event_id": 7
  }
}
```

**Example — response correction (server → client):**

```json
{
  "type": "agent_response_correction",
  "agent_response_correction_event": {
    "original_agent_response": "Old text",
    "corrected_agent_response": "Updated text"
  }
}
```

#### Other types you may see

| `type` | Purpose |
|--------|---------|
| `client_tool_call` | Agent requests a client-side tool |
| `contextual_update` | Contextual text update |
| `vad_score` | Voice-activity score |
| `internal_tentative_agent_response` | Tentative / partial agent text |

---

### Phase 6 — Ending the call

| Step | Who | What happens |
|------|-----|----------------|
| 1 | User | Clicks **End Conversation** (or closes the tab) |
| 2 | Browser | Stops microphone tracks, closes `AudioContext`, closes the WebSocket to `/ws` |
| 3 | App | Stops threads and the asyncio loop; upstream ElevenLabs WebSocket closes |

There is no special “hangup” JSON required for a clean stop in this demo—**closing the browser WebSocket** tears down the proxy session.

---

### End-to-end sequence (simplified)

```
Browser                         App (Flask)                    ElevenLabs
   |                                 |                                |
   |-- WS connect /ws -------------->|                                |
   |-- {"action":"connect"} --------->|-- WSS + xi-api-key ----------->|
   |<-- {"status":"connected"} -------|<-- conversation_initiation_metadata
   |<-- (metadata forwarded) ---------|                                |
   |-- conversation_initiation_client_data --------------------------->|
   |-- user_audio_chunk (repeat) ------------------------------------>|
   |<-- ping ----------------------------------------------------------|
   |-- pong ---------------------------------------------------------->|
   |<-- user_transcript -----------------------------------------------|
   |<-- agent_response ------------------------------------------------|
   |<-- audio (many chunks) -----------------------------------------|
   |                                                                 |
   |-- WS close ---------------------->|-- upstream close ----------->|
```

---

## WebSocket protocol reference (ElevenLabs)

Aligned with [ElevenLabs Agents WebSocket API](https://elevenlabs.io/docs/agents-platform/api-reference/agents-platform/websocket).

### Client → server (publish)

| Message | Purpose |
|---------|---------|
| `user_audio_chunk` | Mic audio as base64 |
| `pong` | Reply to `ping` |
| `conversation_initiation_client_data` | Session / override payload |
| `client_tool_result` | Result of a client tool call |
| `contextual_update` | Extra context text |
| `user_message` | Text-only user message |
| `user_activity` | Activity signal |

### Server → client (subscribe)

| Message | Purpose |
|---------|---------|
| `conversation_initiation_metadata` | IDs and audio formats |
| `user_transcript` | ASR text for user speech |
| `agent_response` | Agent reply text |
| `agent_response_correction` | Corrected agent text |
| `audio` | TTS audio chunks |
| `interruption` | Barge-in / stop current audio |
| `ping` | Keep-alive; respond with `pong` |
| `client_tool_call` | Invoke client tool |
| `contextual_update` | Context from server |
| `vad_score` | VAD signal |
| `internal_tentative_agent_response` | Partial agent text |

## Security Notes

- API keys live in `config.env` (not committed); the browser never receives the ElevenLabs API key
- Use HTTPS and `wss://` in production for the browser ↔ app hop
- Keep your API key confidential and rotate if exposed

## Development

To modify the UI, edit `templates/index.html`
To modify the backend logic, edit `app.py`

## License

MIT License - feel free to use and modify as needed!

