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
- Make sure port 5000 is not in use: `lsof -i :5000`
- Activate the virtual environment: `source venv/bin/activate`
- Reinstall dependencies: `pip install -r requirements.txt`

## WebSocket Protocol

This application implements the ElevenLabs Agent WebSocket protocol:

### Client → Server Messages
- `user_audio_chunk`: Audio data from microphone
- `pong`: Response to ping messages
- `conversation_initiation_client_data`: Initial configuration

### Server → Client Messages
- `conversation_initiation_metadata`: Connection info
- `user_transcript`: Your speech transcribed
- `agent_response`: Agent's text response
- `audio`: Agent's voice audio
- `ping`: Keep-alive messages

## Security Notes

- API keys are sent over WebSocket but not stored
- Use HTTPS in production
- Keep your API key confidential

## Development

To modify the UI, edit `templates/index.html`
To modify the backend logic, edit `app.py`

## License

MIT License - feel free to use and modify as needed!

