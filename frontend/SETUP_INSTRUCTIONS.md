
# Sahayak AI - Setup Instructions

## Overview
Sahayak AI is a voice-controlled digital assistant designed to help senior citizens and visually impaired users with computer tasks. The system consists of a React frontend and a FastAPI backend.

## Frontend Setup (Already Complete)

The frontend is already set up in this Lovable project with:
- Beautiful, accessible voice interface
- Real-time visual feedback
- Large, clear buttons for easy interaction
- Responsive design with smooth animations

## Backend Setup (FastAPI Server)

### Prerequisites
1. Python 3.8 or higher
2. pip package manager

### Installation Steps

1. **Create a virtual environment** (recommended):
   ```bash
   python -m venv sahayak_env
   source sahayak_env/bin/activate  # On Windows: sahayak_env\Scripts\activate
   ```

2. **Install required packages**:
   ```bash
   pip install fastapi uvicorn python-multipart requests pyaudio pygame
   ```

3. **Get the FastAPI backend file**:
   - Copy the `fastapi_backend.py` file from this project
   - Save it in your local directory

4. **Configure your API key**:
   - Open `fastapi_backend.py`
   - Replace `"your_sarvam_api_key_here"` with your actual Sarvam API key

5. **Integrate your VoiceInterface class**:
   - Copy your existing `VoiceInterface` class into the same directory
   - Uncomment the import lines in `fastapi_backend.py`
   - Uncomment the voice_interface initialization in the startup_event

### Running the Backend

1. **Start the FastAPI server**:
   ```bash
   uvicorn fastapi_backend:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Verify it's working**:
   - Open http://localhost:8000/docs in your browser
   - You should see the API documentation

## Integration Steps

### Step 1: Update the Frontend API calls

In your Lovable project, update the `processAudio` function in `src/pages/Index.tsx`:

```typescript
const processAudio = async (audioBlob: Blob) => {
  try {
    setSession(prev => ({ ...prev, isProcessing: true }));
    
    // Call the actual FastAPI backend
    const result = await voiceAPI.processVoiceCommand({
      audio: audioBlob,
      sessionId: sessionIdRef.current
    });
    
    if (result.status === 'success') {
      setSession(prev => ({ 
        ...prev, 
        transcript: result.transcript || '',
        response: result.responseText || '',
        isProcessing: false,
        isPlaying: true 
      }));
      
      // Play the audio response if available
      if (result.audioResponse) {
        await playAudioFromBase64(result.audioResponse);
      }
      
      setSession(prev => ({ ...prev, isPlaying: false }));
      
      // Update session ID
      if (result.agentResult?.sessionId) {
        sessionIdRef.current = result.agentResult.sessionId;
      }
    } else {
      throw new Error(result.error || 'Unknown error');
    }
    
  } catch (error) {
    console.error('Error processing audio:', error);
    setSession(prev => ({ 
      ...prev, 
      isProcessing: false, 
      error: 'Failed to process audio command' 
    }));
  }
};
```

### Step 2: Add Audio Playback Function

Add this function to handle base64 audio playback:

```typescript
const playAudioFromBase64 = async (base64Audio: string) => {
  try {
    const audioData = base64ToArrayBuffer(base64Audio);
    const audioContext = new AudioContext();
    const audioBuffer = await audioContext.decodeAudioData(audioData);
    const source = audioContext.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(audioContext.destination);
    source.start();
    
    return new Promise<void>((resolve) => {
      source.onended = () => resolve();
    });
  } catch (error) {
    console.error('Error playing audio:', error);
  }
};

const base64ToArrayBuffer = (base64: string): ArrayBuffer => {
  const binaryString = window.atob(base64);
  const bytes = new Uint8Array(binaryString.length);
  for (let i = 0; i < binaryString.length; i++) {
    bytes[i] = binaryString.charCodeAt(i);
  }
  return bytes.buffer;
};
```

## Testing the Complete System

1. **Start the FastAPI backend**:
   ```bash
   uvicorn fastapi_backend:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Open the frontend**: Your Lovable project should automatically connect to the backend

3. **Test voice interaction**:
   - Click the microphone button
   - Speak a command
   - Watch for visual feedback and listen for the response

## Troubleshooting

### Common Issues

1. **CORS errors**: Make sure the frontend URL is added to the CORS allowed origins in `fastapi_backend.py`

2. **Microphone permission**: Ensure your browser has microphone access permissions

3. **API key issues**: Verify your Sarvam API key is correctly set in the backend

4. **Audio format errors**: Ensure the audio recording is in WAV format

### Backend Logs
Monitor the FastAPI server logs for detailed error information:
```bash
# The server will show detailed logs when running with --reload
```

### Frontend Debugging
Check the browser console for any JavaScript errors or network issues.

## Production Deployment

For production deployment:

1. **Backend**: Deploy the FastAPI server to a cloud service (AWS, Google Cloud, etc.)
2. **Frontend**: Update the API base URL in `VoiceAPI.ts` to point to your production backend
3. **HTTPS**: Ensure both frontend and backend use HTTPS for microphone access
4. **Environment Variables**: Use environment variables for API keys and configuration

## Features

- 🎤 **Voice Input**: High-quality speech recognition
- 🤖 **AI Processing**: Intelligent command understanding and execution
- 🔊 **Voice Output**: Clear text-to-speech responses
- ♿ **Accessibility**: Designed for senior citizens and visually impaired users
- 📱 **Responsive**: Works on desktop, tablet, and mobile devices
- 🎨 **Beautiful UI**: Modern, calming interface with smooth animations

## Next Steps

1. Integrate your existing computer automation agent
2. Add more voice commands and capabilities
3. Implement user sessions and preferences
4. Add multi-language support
5. Enhance error handling and recovery
6. Add analytics and usage tracking
```

Let me also create a utility file for audio handling:

<lov-write file_path="src/utils/audioUtils.ts">
/**
 * Audio utility functions for voice interface
 */

export const playAudioFromBase64 = async (base64Audio: string): Promise<void> => {
  try {
    const audioData = base64ToArrayBuffer(base64Audio);
    const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
    const audioBuffer = await audioContext.decodeAudioData(audioData);
    const source = audioContext.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(audioContext.destination);
    source.start();
    
    return new Promise<void>((resolve) => {
      source.onended = () => resolve();
    });
  } catch (error) {
    console.error('Error playing audio:', error);
    throw error;
  }
};

export const base64ToArrayBuffer = (base64: string): ArrayBuffer => {
  const binaryString = window.atob(base64);
  const bytes = new Uint8Array(binaryString.length);
  for (let i = 0; i < binaryString.length; i++) {
    bytes[i] = binaryString.charCodeAt(i);
  }
  return bytes.buffer;
};

export const blobToBase64 = (blob: Blob): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result as string;
      const base64 = result.split(',')[1]; // Remove data:audio/wav;base64, prefix
      resolve(base64);
    };
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
};

export const checkMicrophonePermission = async (): Promise<boolean> => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    stream.getTracks().forEach(track => track.stop());
    return true;
  } catch (error) {
    console.error('Microphone permission denied:', error);
    return false;
  }
};
