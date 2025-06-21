"""
Example client for Computer Use OOTB FastAPI endpoints
"""

import requests
import json
import time

# Base URL for your FastAPI server
BASE_URL = "http://localhost:7888"

def create_session_with_config():
    """Create a new session with configuration"""
    config = {
        "planner_model": "gpt-4o",
        "actor_model": "ShowUI",
        "planner_provider": "openai",
        "actor_provider": "local",
        "openai_api_key": "your-openai-api-key-here",  # Replace with your actual API key
        "only_n_most_recent_images": 5,
        "custom_system_prompt": "You are a helpful AI assistant that can control computers.",
        "max_pixels": 1344,
        "awq_4bit": False
    }
    
    response = requests.post(f"{BASE_URL}/session/create", json={"config": config})
    if response.status_code == 200:
        session_data = response.json()
        print(f"✅ Created session: {session_data['session_id']}")
        return session_data["session_id"]
    else:
        print(f"❌ Failed to create session: {response.text}")
        return None

def send_chat_message(session_id, message):
    """Send a chat message to the session"""
    payload = {
        "message": message,
        "session_id": session_id
    }
    
    response = requests.post(f"{BASE_URL}/chat", json=payload)
    if response.status_code == 200:
        chat_response = response.json()
        print(f"🤖 Assistant: {chat_response['response']}")
        return chat_response
    else:
        print(f"❌ Failed to send message: {response.text}")
        return None

def get_session_info(session_id):
    """Get session information"""
    response = requests.get(f"{BASE_URL}/session/{session_id}")
    if response.status_code == 200:
        session_info = response.json()
        print(f"📊 Session Info: {json.dumps(session_info['state'], indent=2)}")
        return session_info
    else:
        print(f"❌ Failed to get session info: {response.text}")
        return None

def get_available_screens():
    """Get available screens"""
    response = requests.get(f"{BASE_URL}/screens")
    if response.status_code == 200:
        screens = response.json()
        print(f"🖥️  Available screens: {screens}")
        return screens
    else:
        print(f"❌ Failed to get screens: {response.text}")
        return None

def health_check():
    """Check API health"""
    response = requests.get(f"{BASE_URL}/health")
    if response.status_code == 200:
        health = response.json()
        print(f"💚 Health Check: {health}")
        return health
    else:
        print(f"❌ Health check failed: {response.text}")
        return None

def main():
    """Main example function"""
    print("🚀 Computer Use OOTB API Client Example")
    print("=" * 50)
    
    # Health check
    print("\n1. Health Check:")
    health_check()
    
    # Get available screens
    print("\n2. Available Screens:")
    get_available_screens()
    
    # Create session
    print("\n3. Creating Session:")
    session_id = create_session_with_config()
    
    if not session_id:
        print("Failed to create session. Exiting.")
        return
    
    # Get session info
    print("\n4. Session Information:")
    get_session_info(session_id)
    
    # Send chat messages
    print("\n5. Chat Examples:")
    
    # Example 1: Simple task
    print("\n📝 Example 1: Simple screenshot task")
    send_chat_message(session_id, "Take a screenshot of the current screen")
    
    time.sleep(2)  # Wait for processing
    
    # Example 2: More complex task
    print("\n📝 Example 2: Complex task")
    send_chat_message(session_id, "Open a text editor and write 'Hello World'")
    
    print("\n✅ Example completed!")
    print(f"Session ID: {session_id}")
    print("You can continue using this session ID for more interactions.")

if __name__ == "__main__":
    main() 