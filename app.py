import asyncio
import json
import os
from flask import Flask, render_template
from flask_sock import Sock
import websockets
from queue import Queue
import threading
from dotenv import load_dotenv

# Load environment variables
load_dotenv('config.env')

# Get credentials from environment
AGENT_ID = os.getenv('AGENT_ID')
API_KEY = os.getenv('API_KEY')

if not AGENT_ID or not API_KEY or API_KEY == 'your_api_key_here':
    print("⚠️  WARNING: Please set AGENT_ID and API_KEY in config.env file!")

app = Flask(__name__)
sock = Sock(app)

@app.route('/')
def index():
    return render_template('index.html')

@sock.route('/ws')
def websocket_proxy(client_ws):
    """Proxy WebSocket connection between client and ElevenLabs"""
    print("🔗 New client connection")
    
    # Use credentials from environment
    agent_id = AGENT_ID
    api_key = API_KEY
    
    if not agent_id or not api_key or api_key == 'your_api_key_here':
        error_msg = 'Server not configured. Please set credentials in config.env file.'
        print(f"❌ {error_msg}")
        client_ws.send(json.dumps({'error': error_msg}))
        return
    
    print(f"📋 Using Agent ID: {agent_id[:20]}...")
    
    # Wait for client ready signal
    try:
        ready_msg = client_ws.receive()
        ready = json.loads(ready_msg)
        if ready.get('action') != 'connect':
            return
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return
    
    # Queues for communication between threads
    client_to_elevenlabs = Queue()
    elevenlabs_to_client = Queue()
    should_stop = threading.Event()
    
    # Thread to read from client WebSocket
    def read_from_client():
        try:
            while not should_stop.is_set():
                try:
                    msg = client_ws.receive(timeout=0.1)
                    if msg:
                        client_to_elevenlabs.put(msg)
                except Exception:
                    pass
        except Exception as e:
            print(f"❌ Read from client error: {e}")
        finally:
            should_stop.set()
    
    # Thread to write to client WebSocket
    def write_to_client():
        try:
            while not should_stop.is_set():
                try:
                    if not elevenlabs_to_client.empty():
                        msg = elevenlabs_to_client.get(timeout=0.1)
                        client_ws.send(msg)
                except Exception:
                    pass
        except Exception as e:
            print(f"❌ Write to client error: {e}")
        finally:
            should_stop.set()
    
    # Async function to handle ElevenLabs connection
    async def elevenlabs_handler():
        uri = f"wss://api.elevenlabs.io/v1/convai/conversation?agent_id={agent_id}"
        headers = {"xi-api-key": api_key}
        
        print(f"🌐 Connecting to ElevenLabs...")
        
        try:
            async with websockets.connect(uri, extra_headers=headers, ping_interval=20) as elevenlabs_ws:
                print("✅ Connected to ElevenLabs")
                
                # Send connection success to client
                elevenlabs_to_client.put(json.dumps({'status': 'connected'}))
                
                async def send_to_elevenlabs():
                    """Send messages from client to ElevenLabs"""
                    try:
                        while not should_stop.is_set():
                            if not client_to_elevenlabs.empty():
                                msg = client_to_elevenlabs.get()
                                await elevenlabs_ws.send(msg)
                                
                                # Log what we're sending
                                try:
                                    data = json.loads(msg)
                                    msg_type = data.get('type', 'unknown')
                                    if msg_type != 'user_audio_chunk':
                                        print(f"📤 Sent to ElevenLabs: {msg_type}")
                                except:
                                    pass
                            else:
                                await asyncio.sleep(0.01)
                    except Exception as e:
                        print(f"❌ Send to ElevenLabs error: {e}")
                        should_stop.set()
                
                async def receive_from_elevenlabs():
                    """Receive messages from ElevenLabs and forward to client"""
                    try:
                        async for message in elevenlabs_ws:
                            # Parse message to log it
                            try:
                                data = json.loads(message)
                                msg_type = data.get('type', 'unknown')
                                print(f"📥 Received from ElevenLabs: {msg_type}")
                                
                                if msg_type == 'audio':
                                    audio_len = len(data.get('audio_event', {}).get('audio_base_64', ''))
                                    print(f"   🔊 Audio chunk: {audio_len} chars")
                            except:
                                pass
                            
                            # Forward to client
                            elevenlabs_to_client.put(message)
                    except Exception as e:
                        print(f"❌ Receive from ElevenLabs error: {e}")
                        should_stop.set()
                
                # Run both async tasks
                await asyncio.gather(
                    send_to_elevenlabs(),
                    receive_from_elevenlabs()
                )
                
        except Exception as e:
            print(f"❌ ElevenLabs connection error: {e}")
            elevenlabs_to_client.put(json.dumps({'error': f'ElevenLabs connection failed: {str(e)}'}))
            should_stop.set()
    
    # Start threads
    client_reader = threading.Thread(target=read_from_client, daemon=True)
    client_writer = threading.Thread(target=write_to_client, daemon=True)
    
    client_reader.start()
    client_writer.start()
    
    # Run async ElevenLabs handler in new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(elevenlabs_handler())
    except Exception as e:
        print(f"❌ Handler error: {e}")
    finally:
        should_stop.set()
        loop.close()
        print("🔌 Connection closed")

if __name__ == '__main__':
    print("🚀 Starting server on http://localhost:5001")
    app.run(host='0.0.0.0', port=5001, debug=True)
