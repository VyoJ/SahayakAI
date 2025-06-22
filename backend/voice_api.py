from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import tempfile
import os
import base64
from typing import Dict, Any
from voice_interface import VoiceInterface
from computer_use_agent.agent import execute_computer_task
from pydantic import BaseModel

app = FastAPI(title="Voice Interface API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize voice interface
API_KEY = os.getenv("SARVAM_API_KEY", "sk_hyoetlfc_7gigQOMrR9Yby0zmprunvyb2")
voice_interface = VoiceInterface(API_KEY)


class TextToSpeechRequest(BaseModel):
    text: str
    language_code: str = "en-IN"


@app.post("/voice/process")
async def process_voice_command(audio_file: UploadFile = File(...)):
    """
    Process voice command: STT -> Agent -> TTS
    """
    if not audio_file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="File must be an audio file")

    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
        content = await audio_file.read()
        temp_file.write(content)
        temp_audio_path = temp_file.name

    try:
        # Process STT
        asr_result = voice_interface.speech_to_text(temp_audio_path)

        if "error" in asr_result:
            raise HTTPException(status_code=400, detail=asr_result["error"])

        transcript = asr_result.get("transcript", "")
        detected_language = asr_result.get("language_code", "en")

        if not transcript:
            raise HTTPException(status_code=400, detail="No speech detected")

        # Process with agent - use the retry method from voice_interface
        agent_result = voice_interface.execute_computer_task_with_retry(transcript)
        print(f"Agent result: {agent_result}")

        # Extract clean text response using the new method
        response_text = voice_interface.extract_text_only_response(agent_result)
        print(f"Response text: {response_text}")

        # Generate TTS
        tts_language_code = voice_interface.map_language_code_for_tts(detected_language)
        tts_audio_file = voice_interface.text_to_speech(
            response_text, tts_language_code
        )

        if not tts_audio_file:
            raise HTTPException(
                status_code=500, detail="Failed to generate speech response"
            )

        # Read TTS audio as base64
        with open(tts_audio_file, "rb") as f:
            audio_base64 = base64.b64encode(f.read()).decode()

        # Cleanup
        os.unlink(tts_audio_file)

        return {
            "transcript": transcript,
            "detected_language": detected_language,
            "response_text": response_text,
            "audio_base64": audio_base64,
            "agent_result": agent_result,
        }

    finally:
        # Cleanup uploaded file
        os.unlink(temp_audio_path)


@app.post("/voice/text-to-speech")
async def text_to_speech(request: TextToSpeechRequest):
    """
    Convert text to speech
    """
    tts_audio_file = voice_interface.text_to_speech(request.text, request.language_code)

    if not tts_audio_file:
        raise HTTPException(status_code=500, detail="Failed to generate speech")

    try:
        with open(tts_audio_file, "rb") as f:
            audio_base64 = base64.b64encode(f.read()).decode()

        return {
            "audio_base64": audio_base64,
            "text": request.text,
            "language_code": request.language_code,
        }
    finally:
        os.unlink(tts_audio_file)


@app.post("/voice/speech-to-text")
async def speech_to_text(audio_file: UploadFile = File(...)):
    """
    Convert speech to text
    """
    if not audio_file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="File must be an audio file")

    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
        content = await audio_file.read()
        temp_file.write(content)
        temp_audio_path = temp_file.name

    try:
        asr_result = voice_interface.speech_to_text(temp_audio_path)

        if "error" in asr_result:
            raise HTTPException(status_code=400, detail=asr_result["error"])

        return asr_result

    finally:
        os.unlink(temp_audio_path)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
