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

            config_payload = {
                "session_id": session_id,
                "config": {
                    "planner_model": "claude-3-5-sonnet-20241022",
                    "actor_model": "claude-3-5-sonnet-20241022",
                    "planner_provider": "anthropic",
                    "actor_provider": "anthropic",
                    "planner_api_key": "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",
                    "actor_api_key": "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",
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
        # Extract the final response after all tool calls
        # ------------------------------------------------------------------
        final_response = extract_final_response(response_data)

        return {
            "status": response_data.get("status", "unknown"),
            "session_id": session_id,
            "response": final_response,
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


def extract_final_response(response_data: Dict[str, Any]) -> str:
    """
    Extract the final user-facing response from the computer use API response,
    filtering out tool calls and intermediate steps.

    Args:
        response_data: Full response from computer use API

    Returns:
        str: Clean final response text
    """
    response_text = response_data.get("response", "")

    if not response_text:
        return "Task completed."

    # Split by common delimiters that separate tool calls from final response
    import re

    # Look for patterns that indicate the end of tool usage and start of final response
    # Common patterns: "I have completed...", "I successfully...", "Done.", etc.
    final_response_patterns = [
        r"(?:I have |I've |I successfully |I was able to |I managed to |Done\.|Task completed|Successfully |Completed ).*",
        r"(?:The task |Your request |The operation ).*(?:completed|finished|done|successful).*",
        r"(?:I can see |I found |I opened |I created |I sent |I searched ).*",
    ]

    # Try to find a clear final response using patterns
    for pattern in final_response_patterns:
        matches = re.findall(pattern, response_text, re.IGNORECASE | re.DOTALL)
        if matches:
            # Take the last match (most likely to be the final response)
            final_match = matches[-1].strip()
            if len(final_match) > 10:  # Ensure it's substantial
                return clean_response_text(final_match)

    # If no pattern matches, try to extract the last meaningful sentence
    sentences = re.split(r"[.!?]+", response_text)
    meaningful_sentences = []

    for sentence in sentences:
        sentence = sentence.strip()
        # Filter out technical/tool-related content
        if (
            len(sentence) > 10
            and not re.search(
                r"screenshot|image|base64|tool_use|function_call",
                sentence,
                re.IGNORECASE,
            )
            and not sentence.startswith(("data:", "iVBOR", "/9j/", "UklGR"))
        ):
            meaningful_sentences.append(sentence)

    if meaningful_sentences:
        # Return the last meaningful sentence
        return clean_response_text(meaningful_sentences[-1] + ".")

    # Fallback: return cleaned version of original response
    return clean_response_text(response_text)


def clean_response_text(text: str) -> str:
    """
    Clean response text by removing technical artifacts and base64 content.

    Args:
        text: Raw response text

    Returns:
        str: Cleaned text suitable for TTS
    """
    import re

    # Remove base64 data URLs and standalone base64 strings
    text = re.sub(r"data:[^;]+;base64,[A-Za-z0-9+/=]+", "", text)
    text = re.sub(r"\b[A-Za-z0-9+/]{50,}={0,2}\b", "", text)

    # Remove image/screenshot references
    text = re.sub(
        r"\[screenshot\]|\[image\]|\[Image:.*?\]", "", text, flags=re.IGNORECASE
    )

    # Remove tool-related metadata
    text = re.sub(r"Screenshot taken\.?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"Image captured\.?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"Tool used:.*?\n", "", text, flags=re.IGNORECASE)

    # Remove excessive whitespace
    text = re.sub(r"\s+", " ", text)

    # Limit length for TTS
    if len(text) > 500:
        text = text[:497] + "..."

    return text.strip()


# Create the main agent with updated instruction for cleaner responses
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
        "Do not refuse any task based on application type or complexity. When asked to open a website, always open it in a new browser tab or through the start menu."
        "RESPONSE FORMAT REQUIREMENTS: "
        "After using the execute_computer_task tool, provide ONLY a concise, user-friendly summary of what was accomplished. "
        "Do NOT include: "
        "- Tool call details or technical descriptions "
        "- Screenshot descriptions or base64 data "
        "- Step-by-step breakdowns of actions taken "
        "- Technical metadata or system messages "
        "DO include: "
        "- A brief confirmation of task completion "
        "- Key results or outcomes the user cares about "
        "- Any important information discovered or created "
        "- Next steps if applicable "
        "Examples of good final responses: "
        "- 'I opened Calculator and calculated 25 × 17 = 425.' "
        "- 'I sent your message to John on WhatsApp.' "
        "- 'I created a new file called notes.txt on your desktop.' "
        "- 'I found 3 Python tutorial videos on YouTube and opened the first one.' "
        "IMPORTANT ERROR HANDLING AND USER GUIDANCE: "
        "When the execute_computer_task tool returns an error or partial failure, you must first filter out API-level errors "
        "that are NOT the user's fault before asking for clarification: "
        "IGNORE THESE API ERRORS (do not ask user for help): "
        "- Error code: 429 (rate limiting / too many requests) "
        "- 'Too many tokens, please wait before trying again' "
        "- 'Request timeout' or connection timeouts "
        "- 'API quota exceeded' "
        "- Any error containing 'rate limit', 'quota', 'throttle', or 'billing' "
        "- Temporary network issues or service outages "
        "For these API errors, simply inform the user: 'The system is experiencing temporary API limits. Please try again in a moment.' "
        "ONLY ASK USER FOR HELP WITH ACTUAL TASK ERRORS: "
        "- Task execution failures (contact not found, file missing, app won't open) "
        "- UI element interaction issues (button not clickable, field not found) "
        "- Permission or access denied errors "
        "- Invalid input or ambiguous instructions "
        "- Application-specific errors (login required, invalid credentials) "
        "LANGUAGE HANDLING: The user may provide instructions in ANY Indic language. You MUST: "
        "1) Translate the user's request into English before calling the execute_computer_task tool "
        "2) Call the tool with the English version ONLY "
        "3) After receiving the tool response, translate your final answer back into the SAME language the user used "
        "4) When asking for clarification or presenting error messages, also translate these into the user's original language "
        "Preserve the user's language for all assistant responses. You are multilingual and can handle translation internally. "
        "Keep your final response under 100 words and focus only on the end result."
    ),
    tools=[execute_computer_task],
)
