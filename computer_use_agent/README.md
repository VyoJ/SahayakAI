# Computer Use ADK Agent

An intelligent Google ADK agent that serves as a natural language interface to the Computer Use API. This agent allows users to control computers and perform any task through simple natural language instructions, powered by Claude 3.7 via AWS Bedrock.

## Features

- **Single Powerful Tool**: One `execute_computer_task` function handles everything
- **Natural Language Interface**: Give any command in plain English
- **Computer Control**: Screenshots, applications, UI interactions, file operations
- **Web Browsing**: Search, navigate, and interact with websites
- **Multi-Step Tasks**: Complex workflows in a single command
- **Session Management**: Maintains context across interactions
- **Error Handling**: Clear error messages and troubleshooting guidance

## Prerequisites

1. **Computer Use API**: Must be running on `localhost:7888`
2. **AWS Bedrock**: Configured with Claude 3.7 access
3. **Google AI Studio API Key**: For the ADK agent
4. **Python 3.8+**: With virtual environment support

## Setup

### 1. Install ADK

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate.bat  # Windows CMD
# .venv\Scripts\Activate.ps1  # Windows PowerShell

# Install Google ADK
pip install google-adk
```

### 2. Configure Environment

Edit `computer_use_agent/.env` and replace `PASTE_YOUR_ACTUAL_API_KEY_HERE` with your Google AI Studio API key:

```env
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GOOGLE_API_KEY=your_actual_api_key_here
```

### 3. Start Computer Use API

In a separate terminal, make sure the Computer Use API is running:

```bash
cd /path/to/computer_use_ootb
python app.py
```

The API should be accessible at `http://localhost:7888`

### 4. Run the Agent

From the parent directory of `computer_use_agent`:

```bash
# Launch the web UI
adk web

# Or use terminal interface
adk run

# Or start API server
adk api_server
```

## Usage

### Web UI (Recommended)

1. Open the URL provided (usually `http://localhost:8000`)
2. Select "computer_use_agent" from the dropdown
3. Start giving natural language commands

### Example Commands

The agent can handle any computer task through natural language. Here are some examples:

#### Basic Tasks
- "Take a screenshot and tell me what's on the screen"
- "Open Calculator"
- "Show me what's in my Downloads folder"

#### Application Control
- "Open Calculator and compute 25 * 17"
- "Launch TextEdit and create a new document"
- "Open Safari and go to news websites"

#### Web & Search
- "Search Google for 'Python programming tutorials'"
- "Open a web browser and find information about machine learning"
- "Go to GitHub and search for React projects"

#### File Operations
- "Create a new text file called 'notes.txt' on the desktop"
- "Open the file manager and navigate to Documents"
- "Create a folder called 'Projects' in my home directory"

#### UI Interactions
- "Click on the search button and type 'hello world'"
- "Scroll down to see more content"
- "Find the settings menu and open it"

#### Complex Multi-Step Tasks
- "Take a screenshot, then open a text editor and write a summary of what I see"
- "Search for Python tutorials, open the first result, and take a screenshot"
- "Open Calculator, compute 15% of 250, then create a text file with the result"
- "Take a screenshot, open a web browser, search for what I see, and summarize the results"

## The Single Tool

### `execute_computer_task(task_description, session_id=None)`

This is the only tool you need! It can handle:

- **Screenshots & Vision**: "Take a screenshot and describe what you see"
- **Application Control**: "Open any application by name"  
- **Web Browsing**: "Search, navigate, and interact with websites"
- **File Operations**: "Create, edit, move, or delete files and folders"
- **UI Interactions**: "Click, type, scroll, and navigate interfaces"
- **System Control**: "Change settings, manage windows, etc."
- **Complex Workflows**: "Multi-step tasks in natural language"

**Examples:**
```python
# Simple task
execute_computer_task("Take a screenshot")

# Complex workflow  
execute_computer_task("Take a screenshot, open Calculator, compute 25*17, then create a text file with the result on the desktop")

# Web interaction
execute_computer_task("Open Safari, search for 'weather in Tokyo', and tell me what you find")
```

## Troubleshooting

### "Could not connect to Computer Use API"
- Ensure the Computer Use API is running on `localhost:7888`
- Start it with: `python app.py`

### "Invalid model identifier" or "Authorization error"
- Check AWS Bedrock configuration
- Ensure Claude 3.7 access is enabled
- Verify AWS credentials are properly configured

### "Agent not found in dropdown"
- Make sure you're running `adk web` from the parent directory of `computer_use_agent`
- Check the project structure is correct

### API Key Issues
- Verify your Google AI Studio API key in `.env`
- Make sure the key has proper permissions

## Architecture

```
User Input (Natural Language)
        ↓
Google ADK Agent (Gemini 2.0)
        ↓
execute_computer_task()
        ↓
Computer Use API (localhost:7888)
        ↓
Claude 3.7 (AWS Bedrock)
        ↓
Computer Actions Executed
        ↓
Results back to User
```

## Advanced Usage

### Session Persistence
The agent automatically manages sessions and maintains context:
```
User: "Take a screenshot"
Agent: [Takes screenshot and describes it]
User: "Now open Calculator"  
Agent: [Opens Calculator, remembering the previous context]
```

### Complex Workflows
You can request complex multi-step operations in a single command:
```
User: "Take a screenshot, analyze what applications are open, then search Google for tutorials about the main application I'm using"
```

### Error Recovery
If something goes wrong, the agent provides clear feedback:
```
Agent: "I encountered an error opening that application. It might not be installed. Would you like me to search for similar applications or try a different approach?"
```

## Testing

Run the test script to verify everything works:
```bash
python test_computer_use_agent.py
```

## Contributing

To extend the agent's capabilities, you can:

1. Modify the `execute_computer_task` function in `agent.py`
2. Update the agent's instructions for better task handling
3. Test with various natural language inputs
4. Improve error handling and user feedback

## License

This project is part of the Computer Use OOTB framework. 