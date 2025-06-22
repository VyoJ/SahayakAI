import requests
import pyaudio
import wave
import threading
import base64
import io
import tempfile
import os
import time
from typing import Optional, Dict, Any
import pygame
from computer_use_agent.agent import execute_computer_task


class VoiceInterface:
    def __init__(self, api_key: str):
        """
        Initialize the voice interface with Sarvam API key.

        Args:
            api_key (str): Sarvam API subscription key
        """
        self.api_key = api_key
        self.sarvam_base_url = "https://api.sarvam.ai"
        self.session_id = None

        # Audio recording parameters
        self.chunk = 1024
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000  # Using 16kHz as recommended by Sarvam docs
        self.record_seconds = 5  # Default recording duration

        # Initialize pygame mixer for audio playback
        pygame.mixer.init()

        # Recording state
        self.is_recording = False
        self.audio_data = []

    def start_recording(self, duration: int = 5) -> str:
        """
        Record audio from microphone and save to temporary file.

        Args:
            duration (int): Recording duration in seconds

        Returns:
            str: Path to the recorded audio file
        """
        print(f"🎤 Recording for {duration} seconds... Speak now!")

        p = pyaudio.PyAudio()

        stream = p.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk,
        )

        frames = []

        for i in range(0, int(self.rate / self.chunk * duration)):
            data = stream.read(self.chunk)
            frames.append(data)

        print("🔴 Recording finished!")

        stream.stop_stream()
        stream.close()
        p.terminate()

        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        temp_filename = temp_file.name
        temp_file.close()

        wf = wave.open(temp_filename, "wb")
        wf.setnchannels(self.channels)
        wf.setsampwidth(p.get_sample_size(self.format))
        wf.setframerate(self.rate)
        wf.writeframes(b"".join(frames))
        wf.close()

        return temp_filename

    def speech_to_text(self, audio_file_path: str) -> Dict[str, Any]:
        """
        Convert speech to text using Sarvam ASR.

        Args:
            audio_file_path (str): Path to the audio file

        Returns:
            Dict[str, Any]: ASR response containing transcript and language code
        """
        try:
            with open(audio_file_path, "rb") as audio_file:
                files = {
                    "file": (os.path.basename(audio_file_path), audio_file, "audio/wav")
                }

                # Use the latest model for better accuracy
                data = {
                    "model": "saarika:v2.5",
                    "language_code": "unknown",  # Let API detect language
                    "with_timestamps": "true",
                }

                headers = {"api-subscription-key": self.api_key}

                response = requests.post(
                    f"{self.sarvam_base_url}/speech-to-text",
                    headers=headers,
                    files=files,
                    data=data,
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    return {
                        "error": f"ASR failed with status {response.status_code}: {response.text}"
                    }
        except Exception as e:
            return {"error": f"ASR error: {str(e)}"}

    def text_to_speech(self, text: str, language_code: str = "en-IN") -> Optional[str]:
        """
        Convert text to speech using Sarvam TTS.

        Args:
            text (str): Text to convert to speech
            language_code (str): Target language code (default: en-IN)

        Returns:
            Optional[str]: Path to the generated audio file, or None if failed
        """
        try:
            headers = {
                "api-subscription-key": self.api_key,
                "Content-Type": "application/json",
            }
            print(f"Received text for TTS: {text}")
            payload = {
                "inputs": [text],
                "target_language_code": language_code,
                "speaker": "meera",  # Use default speaker
                "pitch": 0,
                "pace": 1.0,
                "loudness": 1.0,
                "speech_sample_rate": 8000,
                "enable_preprocessing": True,
                "model": "bulbul:v1",
            }

            response = requests.post(
                f"{self.sarvam_base_url}/text-to-speech", headers=headers, json=payload
            )

            if response.status_code == 200:
                tts_response = response.json()
                if "audios" in tts_response and len(tts_response["audios"]) > 0:
                    # Decode base64 audio
                    audio_base64 = tts_response["audios"][0]
                    audio_data = base64.b64decode(audio_base64)

                    # Save to temporary file
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
                    temp_file.write(audio_data)
                    temp_file.close()

                    return temp_file.name
                else:
                    print("❌ No audio data received from TTS")
                    return None
            else:
                print(
                    f"❌ TTS failed with status {response.status_code}: {response.text}"
                )
                return None

        except Exception as e:
            print(f"❌ TTS error: {str(e)}")
            return None

    def play_audio(self, audio_file_path: str):
        """
        Play audio file using pygame.

        Args:
            audio_file_path (str): Path to the audio file
        """
        try:
            pygame.mixer.music.load(audio_file_path)
            pygame.mixer.music.play()

            # Wait for audio to finish playing
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)

        except Exception as e:
            print(f"❌ Audio playback error: {str(e)}")

    def map_language_code_for_tts(self, stt_language_code: str) -> str:
        """
        Map Sarvam STT language codes to TTS language codes.

        Args:
            stt_language_code (str): Language code from STT

        Returns:
            str: Compatible language code for TTS
        """
        # Map common language codes
        language_mapping = {
            "hi": "hi-IN",
            "en": "en-IN",
            "bn": "bn-IN",
            "gu": "gu-IN",
            "kn": "kn-IN",
            "ml": "ml-IN",
            "mr": "mr-IN",
            "ne": "ne-NP",
            "or": "or-IN",
            "pa": "pa-IN",
            "ta": "ta-IN",
            "te": "te-IN",
            "ur": "ur-IN",
        }

        # Return mapped code or default to English
        return language_mapping.get(stt_language_code, "en-IN")

    def is_api_rate_limit_error(self, error_message: str) -> bool:
        """
        Check if the error is a rate limiting error that should trigger a retry.

        Args:
            error_message (str): Error message to check

        Returns:
            bool: True if it's a rate limiting error
        """
        rate_limit_indicators = [
            "429",
            "rate limit",
            "too many requests",
            "too many tokens",
            "quota exceeded",
            "throttle",
            "billing",
            "rate_limit",
        ]

        error_lower = error_message.lower()
        return any(indicator in error_lower for indicator in rate_limit_indicators)

    def execute_computer_task_with_retry(
        self, transcript: str, max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Execute computer task with automatic retry for rate limiting errors.

        Args:
            transcript (str): The user's command
            max_retries (int): Maximum number of retry attempts

        Returns:
            Dict[str, Any]: Result of the computer task execution
        """
        for attempt in range(max_retries + 1):
            try:
                print(
                    f"🤖 Processing command with computer use agent... (attempt {attempt + 1})"
                )
                agent_result = execute_computer_task(transcript, self.session_id)

                # Update session ID if returned
                if "session_id" in agent_result:
                    self.session_id = agent_result["session_id"]

                # Check if this is a rate limiting error
                error_message = agent_result.get("error_message", "")
                response = agent_result.get("response", "")

                if agent_result.get("status") == "error" and (
                    self.is_api_rate_limit_error(error_message)
                    or self.is_api_rate_limit_error(response)
                ):

                    if attempt < max_retries:
                        wait_time = (
                            2**attempt
                        ) * 5  # Exponential backoff: 5s, 10s, 20s
                        print(
                            f"⏳ Rate limit detected. Waiting {wait_time} seconds before retry..."
                        )
                        time.sleep(wait_time)
                        continue
                    else:
                        print(
                            "⚠️ Maximum retries reached for rate limiting. Continuing with rate limit message."
                        )
                        return {
                            "status": "success",
                            "response": "The system is experiencing temporary API limits. Your request is being processed, please try again in a moment.",
                        }

                # Return successful result or non-rate-limit error
                return agent_result

            except Exception as e:
                error_str = str(e)
                if self.is_api_rate_limit_error(error_str) and attempt < max_retries:
                    wait_time = attempt * 5
                    print(
                        f"⏳ Rate limit detected in exception. Waiting {wait_time} seconds before retry..."
                    )
                    time.sleep(wait_time)
                    continue
                else:
                    return {
                        "status": "error",
                        "error_message": f"Unexpected error: {error_str}",
                    }

        # This should not be reached, but just in case
        return {
            "status": "error",
            "error_message": "Failed to execute task after maximum retries",
        }

    def clean_response_text(self, response_text: str) -> str:
        """
        Clean response text by removing base64 content and other unwanted elements.

        Args:
            response_text (str): Raw response text from the agent

        Returns:
            str: Cleaned text suitable for TTS
        """
        import re

        # Remove base64 data URLs (data:image/png;base64,...)
        response_text = re.sub(
            r"data:[^;]+;base64,[A-Za-z0-9+/=]+", "", response_text
        )

        # Remove standalone base64 strings (long sequences of base64 characters)
        response_text = re.sub(r"\b[A-Za-z0-9+/]{50,}={0,2}\b", "", response_text)

        # Remove image/screenshot references
        response_text = re.sub(
            r"\[screenshot\]|\[image\]|\[Image:.*?\]",
            "",
            response_text,
            flags=re.IGNORECASE,
        )

        # Remove excessive whitespace and newlines
        response_text = re.sub(r"\s+", " ", response_text)

        # Remove common computer use metadata
        response_text = re.sub(
            r"Screenshot taken\.?\s*", "", response_text, flags=re.IGNORECASE
        )
        response_text = re.sub(
            r"Image captured\.?\s*", "", response_text, flags=re.IGNORECASE
        )

        print(f"🔍 Cleaned response text: {response_text[:500]}...")
        return response_text.strip()[:490]

    def extract_text_only_response(self, agent_result: Dict[str, Any]) -> str:
        """
        Extract only the text response from agent result, excluding base64 and metadata.

        Args:
            agent_result (Dict[str, Any]): Full agent response

        Returns:
            str: Clean text response for TTS
        """
        response_text = ""

        if agent_result.get("status") == "success":
            raw_response = agent_result.get("response", "Task completed successfully.")
            response_text = self.clean_response_text(raw_response)

            # If response is empty after cleaning, provide a fallback
            if not response_text or len(response_text.strip()) < 5:
                response_text = "Task completed successfully."

        elif agent_result.get("status") == "error":
            error_msg = agent_result.get("error_message", "Unknown error occurred.")
            response_text = f"I encountered an error: {self.clean_response_text(error_msg)}"
        elif agent_result.get("status") == "connection_error":
            response_text = "I couldn't connect to the computer control system. Please make sure it's running."
        elif agent_result.get("status") == "timeout_error":
            response_text = "The request timed out. Please try again."
        else:
            raw_response = agent_result.get("response", "Task completed.")
            response_text = self.clean_response_text(raw_response)

            # Fallback if response is empty after cleaning
            if not response_text or len(response_text.strip()) < 5:
                response_text = "Task completed."

        return response_text

    def process_voice_command(self, duration: int = 5) -> Dict[str, Any]:
        """
        Complete voice interaction cycle: record -> ASR -> process -> TTS -> play.

        Args:
            duration (int): Recording duration in seconds

        Returns:
            Dict[str, Any]: Result of the voice interaction
        """
        # Step 1: Record audio
        audio_file = self.start_recording(duration)

        try:
            # Step 2: Convert speech to text
            print("🔄 Converting speech to text...")
            asr_result = self.speech_to_text(audio_file)

            if "error" in asr_result:
                return {"status": "error", "message": asr_result["error"]}

            transcript = asr_result.get("transcript", "")
            detected_language = asr_result.get("language_code", "en")

            print(f"🗣️ You said: {transcript}")
            print(f"🌐 Detected language: {detected_language}")

            if not transcript or transcript.strip() == "":
                return {"status": "error", "message": "No speech detected"}

            # Step 3: Process command with computer use agent (with retry logic)
            agent_result = self.execute_computer_task_with_retry(transcript)

            # Step 4: Extract clean text response
            response_text = self.extract_text_only_response(agent_result)

            print(f"🤖 Agent response: {response_text}")

            # Step 5: Convert response to speech in the same language
            print("🔄 Converting response to speech...")
            tts_language_code = self.map_language_code_for_tts(detected_language)
            tts_audio_file = self.text_to_speech(response_text, tts_language_code)

            if tts_audio_file:
                # Step 6: Play response
                print("🔊 Playing response...")
                self.play_audio(tts_audio_file)

                # Cleanup TTS file
                os.unlink(tts_audio_file)
            else:
                print("❌ Failed to generate speech response")
                # Fallback: print the response
                print(f"📝 Response (text): {response_text}")

            return {
                "status": "success",
                "transcript": transcript,
                "detected_language": detected_language,
                "agent_result": agent_result,
                "response_text": response_text,
            }

        finally:
            # Cleanup recorded audio file
            if os.path.exists(audio_file):
                os.unlink(audio_file)

    def interactive_mode(self):
        """
        Start interactive voice mode where user can continuously interact with the agent.
        """
        print("🎙️ Voice Interface Started!")
        print("Commands:")
        print("  - Press ENTER to start recording")
        print("  - Type 'quit' to exit")
        print("  - Type 'duration X' to set recording duration to X seconds")
        print("  - Type 'test' to test TTS with sample text")
        print()

        record_duration = 5

        while True:
            try:
                user_input = input(
                    f"🎤 Press ENTER to record ({record_duration}s) or type command: "
                ).strip()

                if user_input.lower() == "quit":
                    print("👋 Goodbye!")
                    break
                elif user_input.lower().startswith("duration "):
                    try:
                        new_duration = int(user_input.split()[1])
                        if new_duration > 0:
                            record_duration = new_duration
                            print(
                                f"📊 Recording duration set to {record_duration} seconds"
                            )
                        else:
                            print("❌ Duration must be positive")
                    except (IndexError, ValueError):
                        print("❌ Invalid duration format. Use: duration X")
                elif user_input.lower() == "test":
                    # Test TTS functionality
                    test_text = "Hello, this is a test of the text to speech system."
                    print("🔄 Testing TTS...")
                    tts_file = self.text_to_speech(test_text, "en-IN")
                    if tts_file:
                        self.play_audio(tts_file)
                        os.unlink(tts_file)
                        print("✅ TTS test completed")
                    else:
                        print("❌ TTS test failed")
                elif user_input == "":
                    # Start voice interaction
                    result = self.process_voice_command(record_duration)
                    if result["status"] == "error":
                        print(f"❌ Error: {result['message']}")
                    print()
                else:
                    print("❌ Unknown command")

            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {str(e)}")


def main():
    """
    Main function to start the voice interface.
    """
    # Get API key from environment variable or use provided one
    API_KEY = os.getenv("SARVAM_API_KEY", "sk_hyoetlfc_7gigQOMrR9Yby0zmprunvyb2")

    if not API_KEY:
        print(
            "❌ Please set SARVAM_API_KEY environment variable or update the API key in the code"
        )
        return

    # Create voice interface
    voice_interface = VoiceInterface(API_KEY)

    # Start interactive mode
    voice_interface.interactive_mode()


if __name__ == "__main__":
    main()
