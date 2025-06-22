import requests
import json
import time
from typing import Dict, Any, Optional
from google.adk.agents import Agent

# Computer Use API Configuration
COMPUTER_USE_API_URL = "http://localhost:7888"

def execute_computer_task(task_description: str, session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Executes any computer task using the computer use API with Claude 3.7 via Bedrock.
    
    This function can handle all types of computer tasks including:
    - Taking screenshots and describing what's on screen
    - Opening applications (Calculator, Browser, Text Editor, etc.)
    - Performing web searches and browsing websites
    - Interacting with UI elements (clicking, typing, scrolling)
    - File operations (creating, editing, moving files and folders)
    - System navigation and control
    
    Args:
        task_description (str): Natural language description of the task to perform
        session_id (str): Optional session ID to maintain context across tasks
        
    Returns:
        Dict[str, Any]: Result of the computer task execution
        
    Examples:
        - "Take a screenshot and describe what you see"
        - "Open Calculator and compute 25 * 17"
        - "Search Google for 'Python tutorials'"
        - "Create a new text file called 'notes.txt' on the desktop"
        - "Click on the search button and type 'hello world'"
        - "Open Finder and navigate to the Documents folder"
        - "Take a screenshot, then open a web browser and search for news"
    """
    try:
        # Create or get session
        if not session_id:
            # Create new session with Claude 3.7 configuration
            session_response = requests.post(f"{COMPUTER_USE_API_URL}/session/create")
            if session_response.status_code != 200:
                return {
                    "status": "error",
                    "error_message": f"Failed to create session: {session_response.text}"
                }
            
            session_data = session_response.json()
            session_id = session_data["session_id"]
            
            # Configure session for Claude 3.7 via Bedrock
            config_payload = {
                "session_id": session_id,
                "config": {
                    "planner_model": "claude-3-7-sonnet-20250219",
                    "actor_model": "claude-3-7-sonnet-20250219",
                    "planner_provider": "bedrock",
                    "actor_provider": "bedrock",
                    "custom_system_prompt": (
                        "You are a helpful AI assistant that can interact with ANY computer interface and application. "
                        "You have full access to control this computer and can open, interact with, and use ANY application "
                        "installed on the system, including but not limited to: WhatsApp, Telegram, Discord, Slack, email clients, "
                        "web browsers, social media apps, productivity software, games, and any other programs. "
                        "You can send messages, make calls, browse the web, create files, and perform any task the user requests. "
                        "There are no restrictions on which applications you can access - treat all installed software as available tools. "
                        "Execute tasks carefully and provide clear feedback about what you're doing. "
                        "If an application isn't immediately visible, use system search or application launchers to find and open it."
                    )
                }
            }
            
            config_response = requests.post(f"{COMPUTER_USE_API_URL}/session/config", json=config_payload)
            if config_response.status_code != 200:
                return {
                    "status": "error",
                    "error_message": f"Failed to configure session: {config_response.text}"
                }
        
        # Execute the task
        chat_payload = {
            "message": task_description,
            "session_id": session_id
        }
        
        chat_response = requests.post(f"{COMPUTER_USE_API_URL}/chat", json=chat_payload)
        
        if chat_response.status_code != 200:
            return {
                "status": "error",
                "error_message": f"Failed to execute task: {chat_response.text}"
            }
        
        response_data = chat_response.json()
        
        if response_data["status"] == "success":
            return {
                "status": "success",
                "session_id": session_id,
                "status_code": chat_response.status_code,
                "task_completed": True,
                "message": "Task executed successfully"
            }
        else:
            return {
                "status": "error",
                "session_id": session_id,
                "status_code": chat_response.status_code,
                "task_completed": False,
                "message": "Task execution failed"
            }
            
    except requests.exceptions.ConnectionError:
        return {
            "status": "error",
            "error_message": "Could not connect to Computer Use API. Make sure it's running on localhost:7888"
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Unexpected error: {str(e)}"
        }

# Create the main agent with just one powerful tool
root_agent = Agent(
    name="computer_use_agent",
    model="gemini-2.0-flash",
    description=(
        "An intelligent agent that can control computers and perform any task through natural language instructions. "
        "This agent can take screenshots, open applications, browse the web, interact with UI elements, "
        "perform file operations, and execute complex multi-step workflows using Claude 3.7 via AWS Bedrock."
    ),
    instruction=(
        "You are a helpful AI assistant that can control computers and perform any task the user requests. "
        "Use the execute_computer_task tool to handle all user requests, no matter how simple or complex. "
        "You have FULL ACCESS to interact with ANY application on the computer, including messaging apps like WhatsApp, "
        "Telegram, Discord, email clients, social media, productivity software, games, and any other installed programs. "
        "You can open applications, send messages, make calls, browse the web, create files, click buttons, type text, "
        "and perform any computer task the user requests. There are no restrictions on which applications you can use. "
        "Just describe what the user wants in natural language and the tool will execute it using Claude 3.7 via Bedrock. "
        "Always provide clear feedback about what you're doing and whether tasks were completed successfully. "
        "If you encounter errors, explain them clearly and suggest potential solutions."
    ),
    tools=[execute_computer_task],
) 