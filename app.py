"""
FastAPI endpoints for Computer Use OOTB
"""

import platform
import asyncio
import base64
import os
import io
import json
from datetime import datetime
from enum import StrEnum
from functools import partial
from pathlib import Path
from typing import cast, Dict, List, Optional, Any
from PIL import Image

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from anthropic import APIResponse
from anthropic.types import TextBlock
from anthropic.types.beta import BetaMessage, BetaTextBlock, BetaToolUseBlock
from anthropic.types.tool_use_block import ToolUseBlock

from screeninfo import get_monitors
from computer_use_demo.tools.logger import logger, truncate_string

logger.info("Starting the FastAPI app")

screens = get_monitors()
logger.info(f"Found {len(screens)} screens")

from computer_use_demo.loop import APIProvider, sampling_loop_sync

from computer_use_demo.tools import ToolResult
from computer_use_demo.tools.computer import get_screen_details
SCREEN_NAMES, SELECTED_SCREEN_INDEX = get_screen_details()

API_KEY_FILE = "./api_keys.json"

WARNING_TEXT = "⚠️ Security Alert: Do not provide access to sensitive accounts or data, as malicious web content can hijack Agent's behavior. Keep monitor on the Agent's actions."

# FastAPI app instance
app = FastAPI(title="Computer Use OOTB API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state storage (in production, use a proper database)
sessions = {}

# Pydantic models for request/response
class SessionConfig(BaseModel):
    planner_model: str = "gpt-4o"
    actor_model: str = "ShowUI"
    planner_provider: str = "openai"
    actor_provider: str = "local"
    planner_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    qwen_api_key: Optional[str] = None
    ui_tars_url: Optional[str] = None
    selected_screen: int = 0
    only_n_most_recent_images: int = 10
    custom_system_prompt: str = ""
    hide_images: bool = False
    showui_config: str = "Default"
    max_pixels: int = 1344
    awq_4bit: bool = False

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"

class ChatResponse(BaseModel):
    response: str
    session_id: str
    status: str

class ConfigUpdateRequest(BaseModel):
    session_id: str = "default"
    config: Dict[str, Any]

def setup_state(session_id: str = "default"):
    """Initialize session state"""
    if session_id not in sessions:
        sessions[session_id] = {}
    
    state = sessions[session_id]
    
    if "messages" not in state:
        state["messages"] = []
    if "planner_model" not in state:
        state["planner_model"] = "gpt-4o"
    if "actor_model" not in state:
        state["actor_model"] = "ShowUI"
    if "planner_provider" not in state:
        state["planner_provider"] = "openai"
    if "actor_provider" not in state:
        state["actor_provider"] = "local"

    # Fetch API keys from environment variables
    if "openai_api_key" not in state: 
        state["openai_api_key"] = os.getenv("OPENAI_API_KEY", "")
    if "anthropic_api_key" not in state:
        state["anthropic_api_key"] = os.getenv("ANTHROPIC_API_KEY", "")    
    if "qwen_api_key" not in state:
        state["qwen_api_key"] = os.getenv("QWEN_API_KEY", "")
    if "ui_tars_url" not in state:
        state["ui_tars_url"] = ""

    # Set the initial api_key based on the provider
    if "planner_api_key" not in state:
        if state["planner_provider"] == "openai":
            state["planner_api_key"] = state["openai_api_key"]
        elif state["planner_provider"] == "anthropic":
            state["planner_api_key"] = state["anthropic_api_key"]
        elif state["planner_provider"] == "qwen":
            state["planner_api_key"] = state["qwen_api_key"]
        else:
            state["planner_api_key"] = ""

    logger.info(f"loaded initial api_key for {state['planner_provider']}: {state['planner_api_key']}")

    if not state["planner_api_key"]:
        logger.warning("Planner API key not found. Please set it in the environment or via API.")

    if "selected_screen" not in state:
        state['selected_screen'] = SELECTED_SCREEN_INDEX if SCREEN_NAMES else 0

    if "auth_validated" not in state:
        state["auth_validated"] = False
    if "responses" not in state:
        state["responses"] = {}
    if "tools" not in state:
        state["tools"] = {}
    if "only_n_most_recent_images" not in state:
        state["only_n_most_recent_images"] = 10
    if "custom_system_prompt" not in state:
        state["custom_system_prompt"] = ""
        device_os_name = "Windows" if platform.system() == "Windows" else "Mac" if platform.system() == "Darwin" else "Linux"
        state["custom_system_prompt"] += f"\n\nNOTE: you are operating a {device_os_name} machine"
    if "hide_images" not in state:
        state["hide_images"] = False
    if 'chatbot_messages' not in state:
        state['chatbot_messages'] = []
        
    if "showui_config" not in state:
        state["showui_config"] = "Default"
    if "max_pixels" not in state:
        state["max_pixels"] = 1344
    if "awq_4bit" not in state:
        state["awq_4bit"] = False

    return state

def validate_auth(provider: APIProvider, api_key: str | None):
    if provider == APIProvider.ANTHROPIC:
        if not api_key:
            return "Enter your Anthropic API key to continue."
    if provider == APIProvider.BEDROCK:
        import boto3
        if not boto3.Session().get_credentials():
            return "You must have AWS credentials set up to use the Bedrock API."
    if provider == APIProvider.VERTEX:
        import google.auth
        from google.auth.exceptions import DefaultCredentialsError
        if not os.environ.get("CLOUD_ML_REGION"):
            return "Set the CLOUD_ML_REGION environment variable to use the Vertex API."
        try:
            google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        except DefaultCredentialsError:
            return "Your google cloud credentials are not set up correctly."

def _api_response_callback(response: APIResponse[BetaMessage], response_state: dict):
    response_id = datetime.now().isoformat()
    response_state[response_id] = response

def _tool_output_callback(tool_output: ToolResult, tool_id: str, tool_state: dict):
    tool_state[tool_id] = tool_output

def collect_output_messages(messages_list: List):
    """Callback to collect output messages"""
    def callback(message, hide_images=False, sender="bot"):
        def _render_message(message: str | BetaTextBlock | BetaToolUseBlock | ToolResult, hide_images=False):
            logger.info(f"_render_message: {str(message)[:100]}")

            if isinstance(message, str):
                return message
            
            is_tool_result = not isinstance(message, str) and (
                isinstance(message, ToolResult)
                or message.__class__.__name__ == "ToolResult"
                or message.__class__.__name__ == "CLIResult"
            )
            if not message or (
                is_tool_result
                and hide_images
                and not hasattr(message, "error")
                and not hasattr(message, "output")
            ):
                return
            
            if is_tool_result:
                message = cast(ToolResult, message)
                if message.output:
                    return message.output
                if message.error:
                    return f"Error: {message.error}"
                if message.base64_image and not hide_images:
                    return f'<img src="data:image/png;base64,{message.base64_image}">'

            elif isinstance(message, BetaTextBlock) or isinstance(message, TextBlock):
                return message.text
            elif isinstance(message, BetaToolUseBlock) or isinstance(message, ToolUseBlock):
                return f"Tool Use: {message.name}\nInput: {message.input}"
            else:  
                return message

        rendered_message = _render_message(message, hide_images)
        if rendered_message:
            messages_list.append({"sender": sender, "content": rendered_message})
    
    return callback

# API Routes

@app.get("/")
def root():
    """Health check endpoint"""
    return {"message": "Computer Use OOTB API is running", "status": "healthy"}

@app.get("/screens")
def get_screens():
    """Get available screens"""
    screen_options, primary_index = get_screen_details()
    return {
        "screens": screen_options,
        "primary_index": primary_index,
        "total_screens": len(screen_options)
    }

@app.get("/examples")
def get_examples():
    """Get example tasks"""
    try:
        with open("assets/examples/ootb_examples.json", "r") as f:
            examples = json.load(f)
        return examples
    except FileNotFoundError:
        return {"error": "Examples file not found"}

@app.post("/session/create")
def create_session(config: Optional[SessionConfig] = None):
    """Create a new session with optional configuration"""
    session_id = f"session_{datetime.now().isoformat()}"
    setup_state(session_id)
    
    if config:
        update_session_config(ConfigUpdateRequest(
            session_id=session_id,
            config=config.dict()
        ))
    
    return {"session_id": session_id, "status": "created"}

@app.get("/session/{session_id}")
def get_session(session_id: str):
    """Get session state"""
    if session_id not in sessions:
        setup_state(session_id)
    
    state = sessions[session_id]
    # Remove sensitive information
    safe_state = {k: v for k, v in state.items() if "api_key" not in k.lower()}
    safe_state["has_planner_api_key"] = bool(state.get("planner_api_key"))
    
    return {"session_id": session_id, "state": safe_state}

@app.post("/session/config")
def update_session_config(request: ConfigUpdateRequest):
    """Update session configuration"""
    session_id = request.session_id
    if session_id not in sessions:
        setup_state(session_id)
    
    state = sessions[session_id]
    
    # Update state with provided config
    for key, value in request.config.items():
        if key in ["planner_api_key", "openai_api_key", "anthropic_api_key", "qwen_api_key"]:
            # Handle API keys securely
            state[key] = value
        else:
            state[key] = value
    
    logger.info(f"Updated session {session_id} config: {list(request.config.keys())}")
    
    return {"session_id": session_id, "status": "updated"}

@app.post("/chat")
def chat(request: ChatRequest):
    """Process chat message and return response"""
    session_id = request.session_id
    user_input = request.message
    
    if session_id not in sessions:
        setup_state(session_id)
    
    state = sessions[session_id]
    
    try:
        # Append the user message to state["messages"]
        state["messages"].append({
            "role": "user",
            "content": [TextBlock(type="text", text=user_input)],
        })

        # Collect output messages
        output_messages = []
        output_callback = collect_output_messages(output_messages)

        # Run sampling_loop_sync
        responses = []
        for loop_msg in sampling_loop_sync(
            system_prompt_suffix=state["custom_system_prompt"],
            planner_model=state["planner_model"],
            planner_provider=state["planner_provider"],
            actor_model=state["actor_model"],
            actor_provider=state["actor_provider"],
            messages=state["messages"],
            output_callback=output_callback,
            tool_output_callback=partial(_tool_output_callback, tool_state=state["tools"]),
            api_response_callback=partial(_api_response_callback, response_state=state["responses"]),
            api_key=state["planner_api_key"],
            only_n_most_recent_images=state["only_n_most_recent_images"],
            selected_screen=state['selected_screen'],
            showui_max_pixels=state['max_pixels'],
            showui_awq_4bit=state['awq_4bit']
        ):
            if loop_msg is None:
                logger.info("End of task. Close the loop.")
                break
            responses.append(str(loop_msg))

        # Combine all output messages
        full_response = "\n".join([msg["content"] for msg in output_messages if msg["sender"] == "bot"])
        
        if not full_response and responses:
            full_response = "\n".join(responses)
        
        if not full_response:
            full_response = "Task completed successfully."

        return ChatResponse(
            response=full_response,
            session_id=session_id,
            status="success"
        )
    
    except Exception as e:
        logger.error(f"Error processing chat message: {str(e)}")
        return ChatResponse(
            response=f"Error: {str(e)}",
            session_id=session_id,
            status="error"
        )

@app.get("/session/{session_id}/messages")
def get_messages(session_id: str):
    """Get chat messages for a session"""
    if session_id not in sessions:
        return {"messages": []}
    
    state = sessions[session_id]
    return {"messages": state.get("chatbot_messages", [])}

@app.delete("/session/{session_id}")
def delete_session(session_id: str):
    """Delete a session"""
    if session_id in sessions:
        del sessions[session_id]
        return {"session_id": session_id, "status": "deleted"}
    else:
        raise HTTPException(status_code=404, detail="Session not found")

@app.get("/health")
def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "screens_available": len(SCREEN_NAMES),
        "active_sessions": len(sessions),
        "platform": platform.system()
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7888)