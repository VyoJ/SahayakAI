// API service for Sahayak AI backend
const API_BASE_URL = 'http://localhost:8000';

export interface VoiceProcessResponse {
  transcript: string;
  detected_language: string;
  response_text: string;
  audio_base64: string;
  agent_result: {
    status: string;
    message?: string;
    error_message?: string;
    session_id?: string;
  };
}

export interface TTSResponse {
  audio_base64: string;
  text: string;
  language_code: string;
}

export interface STTResponse {
  transcript: string;
  language_code: string;
}

export interface HealthResponse {
  status: string;
  message: string;
}

class ApiService {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  /**
   * Check API health status
   */
  async checkHealth(): Promise<HealthResponse> {
    try {
      // Since there's no health endpoint in the backend, we'll test the main endpoint
      const response = await fetch(`${this.baseUrl}/voice/process`, {
        method: 'OPTIONS'
      });
      if (response.ok || response.status === 405) {
        // 405 Method Not Allowed is fine - it means the endpoint exists
        return { status: 'ok', message: 'API is healthy' };
      }
      throw new Error(`Health check failed: ${response.status}`);
    } catch (error) {
      throw new Error(`Health check failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Process voice command (complete pipeline)
   */
  async processVoice(audioBlob: Blob, sessionId?: string): Promise<VoiceProcessResponse> {
    const formData = new FormData();
    formData.append('audio_file', audioBlob, 'recording.wav');

    const response = await fetch(`${this.baseUrl}/voice/process`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to process voice command');
    }

    return response.json();
  }

  /**
   * Convert text to speech
   */
  async textToSpeech(text: string, languageCode: string = 'en-IN'): Promise<TTSResponse> {
    const requestBody = {
      text: text,
      language_code: languageCode
    };

    const response = await fetch(`${this.baseUrl}/voice/text-to-speech`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to convert text to speech');
    }

    return response.json();
  }

  /**
   * Convert speech to text only
   */
  async speechToText(audioBlob: Blob): Promise<STTResponse> {
    const formData = new FormData();
    formData.append('audio_file', audioBlob, 'recording.wav');

    const response = await fetch(`${this.baseUrl}/voice/speech-to-text`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to convert speech to text');
    }

    return response.json();
  }

  /**
   * Get session information
   */
  async getSession(sessionId: string): Promise<any> {
    const response = await fetch(`${this.baseUrl}/sessions/${sessionId}`);
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Session not found');
    }

    return response.json();
  }

  /**
   * Delete session
   */
  async deleteSession(sessionId: string): Promise<{ message: string }> {
    const response = await fetch(`${this.baseUrl}/sessions/${sessionId}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to delete session');
    }

    return response.json();
  }
}

// Export singleton instance
export const apiService = new ApiService();

// Helper function to convert base64 audio to blob
export const base64ToAudioBlob = (base64: string): Blob => {
  const audioData = atob(base64);
  const audioArray = new Uint8Array(audioData.length);
  for (let i = 0; i < audioData.length; i++) {
    audioArray[i] = audioData.charCodeAt(i);
  }
  return new Blob([audioArray], { type: 'audio/wav' });
};

// Helper function to play audio from base64
export const playBase64Audio = (base64: string): Promise<void> => {
  return new Promise((resolve, reject) => {
    try {
      const audioBlob = base64ToAudioBlob(base64);
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);

      audio.onended = () => {
        URL.revokeObjectURL(audioUrl);
        resolve();
      };

      audio.onerror = (error) => {
        URL.revokeObjectURL(audioUrl);
        reject(error);
      };

      audio.play().catch(reject);
    } catch (error) {
      reject(error);
    }
  });
}; 