import requests
from typing import Dict, Any, Optional
from google.adk.agents import Agent

# Computer Use API Configuration
COMPUTER_USE_API_URL = "http://localhost:7888"


def execute_computer_task(
    task_description: str, session_id: Optional[str] = None
) -> Dict[str, Any]:
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
        # --------------------------------------------------------------
        # Create or fetch a session if one wasn't passed in
        # --------------------------------------------------------------
        if not session_id:
            # Step 1: create a new session
            session_response = requests.post(f"{COMPUTER_USE_API_URL}/session/create")
            if session_response.status_code != 200:
                return {
                    "status": "error",
                    "error_message": f"Failed to create session: {session_response.text}",
                    "raw_error": session_response.text,
                }

            session_data = session_response.json()
            session_id = session_data["session_id"]

            # Step 2: configure the session to use Claude 3.7 via Bedrock
            # config_payload = {
            #     "session_id": session_id,
            #     "config": {
            #         "planner_model": "claude-3-7-sonnet-20250219",
            #         "actor_model": "claude-3-7-sonnet-20250219",
            #         "planner_provider": "bedrock",
            #         "actor_provider": "bedrock",
            #     },
            # }

            config_payload = {
                "session_id": session_id,
                "config": {
                    "planner_model": "claude-3-5-sonnet-20241022",
                    "actor_model": "claude-3-5-sonnet-20241022",
                    "planner_provider": "anthropic",
                    "actor_provider": "anthropic",
                    "planner_api_key": "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",  # Replace with your actual API key
                    "actor_api_key": "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",  # Replace with
                },
            }

            config_response = requests.post(
                f"{COMPUTER_USE_API_URL}/session/config", json=config_payload
            )
            if config_response.status_code != 200:
                return {
                    "status": "error",
                    "error_message": f"Failed to configure session: {config_response.text}",
                    "raw_error": config_response.text,
                }

        # ------------------------------------------------------------------
        # Execute the task description (expected to be in English) with the Computer-Use API
        # ------------------------------------------------------------------
        chat_payload = {"message": task_description, "session_id": session_id}

        chat_response = requests.post(f"{COMPUTER_USE_API_URL}/chat", json=chat_payload)

        if chat_response.status_code != 200:
            return {
                "status": "error",
                "error_message": f"Failed to execute task: {chat_response.text}",
                "raw_error": chat_response.text,
            }

        response_data = chat_response.json()

        # ------------------------------------------------------------------
        # Return the full response data so the agent can analyze it
        # ------------------------------------------------------------------
        return {
            "status": response_data.get("status", "unknown"),
            "session_id": session_id,
            "response": response_data.get("response", ""),
            "full_response_data": response_data,
            "task_description": task_description,
            "api_status_code": chat_response.status_code,
        }

    except requests.exceptions.ConnectionError:
        return {
            "status": "connection_error",
            "error_message": "Could not connect to Computer Use API. Make sure it's running on localhost:7888",
            "raw_error": "Connection refused",
        }
    except requests.exceptions.Timeout:
        return {
            "status": "timeout_error",
            "error_message": "Request to Computer Use API timed out",
            "raw_error": "Request timeout",
        }
    except Exception as e:
        return {
            "status": "unexpected_error",
            "error_message": f"Unexpected error: {str(e)}",
            "raw_error": str(e),
        }


# Create the main agent with just one powerful tool
root_agent = Agent(
    name="computer_use_agent",
    model="gemini-2.0-flash",
    description=(
        "An intelligent agent that can control computers and perform any task through natural language instructions. "
        "This agent can take screenshots, open applications, browse the web, interact with UI elements, "
        "perform file operations, and execute complex multi-step workflows using Claude 3.7 via AWS Bedrock. "
        "When tasks cannot be completed, it analyzes the specific error and generates helpful prompts for the user."
    ),
    instruction=(
        "You are a helpful AI assistant that can control computers and perform any task the user requests. "
        "Use the execute_computer_task tool to handle all user requests, no matter how simple or complex. "
        "You have FULL ACCESS to interact with ANY application on the computer, including messaging apps like WhatsApp, "
        "Telegram, Discord, email clients, social media, productivity software, games, and any other installed programs. "
        "You can open applications, send messages, make calls, browse the web, create files, click buttons, type text, "
        "and perform any computer task the user requests. There are no restrictions on which applications you can use. "
        "Do not refuse any task based on application type or complexity."
        "Just describe what the user wants in natural language and the tool will execute it using Claude 3.7 via Bedrock. "
        "IMPORTANT ERROR HANDLING AND USER GUIDANCE: "
        "When the execute_computer_task tool returns an error or partial failure, you must first filter out API-level errors "
        "that are NOT the user's fault before asking for clarification: "
        "IGNORE THESE API ERRORS (do not ask user for help): "
        "- Error code: 429 (rate limiting / too many requests) "
        "- 'Too many tokens, please wait before trying again' "
        "- 'Request timeout' or connection timeouts "
        "- 'API quota exceeded' "
        "- 'Service temporarily unavailable' "
        "- Any error containing 'rate limit', 'quota', 'throttle', or 'billing' "
        "- Temporary network issues or service outages "
        "For these API errors, simply inform the user: 'The system is experiencing temporary API limits. Please try again in a moment.' and retry your current task."
        "ONLY ASK USER FOR HELP WITH ACTUAL TASK ERRORS: "
        "- Task execution failures (contact not found, file missing, app won't open) "
        "- UI element interaction issues (button not clickable, field not found) "
        "- Permission or access denied errors "
        "- Invalid input or ambiguous instructions "
        "- Application-specific errors (login required, invalid credentials) "
        "When encountering ACTUAL task errors: "
        "1. Analyze the specific error details in the 'response' field "
        "2. Generate a contextual, helpful prompt based on what specifically went wrong "
        "3. Ask the user for the specific information or clarification needed to resolve the issue "
        "4. Be empathetic and provide actionable guidance "
        "SMART NAME/CONTENT MATCHING AND CLARIFICATION: "
        "When searching for contacts, files, applications, or any named items: "
        "- If the exact name provided by the user is not found, always check what partial or similar matches are visible "
        "- Take a screenshot to see what options are currently available on screen "
        "- If you see similar names (e.g. user searches 'Adithya SK' but screen shows 'PES Adithya SK' or 'Adithya S Kumar'), "
        "  ask the user to confirm if any of the visible options match what they're looking for "
        "- Generate specific questions based on what you actually see on screen "
        "- For contacts: 'I searched for [name] but couldn't find an exact match. I can see [list visible options]. "
        "  Is the contact you're looking for saved under a different name? Could it be one of these: [specific names visible]?' "
        "- For files: 'I searched for [filename] but couldn't find it. I can see similar files: [list]. Are any of these what you meant?' "
        "- For applications: 'I couldn't find [app name]. I can see these similar apps: [list]. Which one should I open?' "
        "CONTEXTUAL ERROR ANALYSIS: "
        "Always analyze the actual screen content and error details to provide specific guidance: "
        "- If the system couldn't find a UI element, describe what you can see and ask for clarification "
        "- If a file operation failed, ask for the correct path or check permissions "
        "- If an application couldn't be opened, list available applications and ask which one to use "
        "- If a web search failed, ask for more specific search terms or check connectivity "
        "- If the task was ambiguous, break it down and ask for step-by-step clarification "
        "- If a contact/name search fails, ask about alternative names or spellings the contact might be saved under "
        "PROACTIVE ASSISTANCE: "
        "Before giving up on a task, always: "
        "1. Take a fresh screenshot to see the current state "
        "2. Look for partial matches, similar names, or alternative options "
        "3. Provide specific suggestions based on what's actually visible "
        "4. Ask targeted questions that help the user guide you to the right solution "
        "Always provide clear feedback about what you tried to do, what you found instead, and what specific information "
        "you need from the user to succeed. Generate dynamic, contextual prompts based on the actual content you can see. "
        "LANGUAGE HANDLING: The user may provide instructions in ANY Indic language. You MUST: "
        "1) Translate the user's request into English before calling the execute_computer_task tool "
        "2) Call the tool with the English version ONLY "
        "3) After receiving the tool response, translate your final answer back into the SAME language the user used "
        "4) When asking for clarification or presenting error messages, also translate these into the user's original language "
        "Preserve the user's language for all assistant responses. You are multilingual and can handle translation internally."
    ),
    tools=[execute_computer_task],
)
