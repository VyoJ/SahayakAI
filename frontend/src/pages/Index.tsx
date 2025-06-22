import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Mic, MicOff, Play } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import VoiceParticles from '@/components/VoiceParticles';
import WaveformVisualizer from '@/components/WaveformVisualizer';
import { apiService, playBase64Audio } from '@/lib/api';

interface VoiceSession {
  isRecording: boolean;
  isProcessing: boolean;
  isPlaying: boolean;
  transcript: string;
  response: string;
  error: string;
  sessionId?: string;
  languageCode?: string;
}

const Index = () => {
  const { toast } = useToast();
  const [session, setSession] = useState<VoiceSession>({
    isRecording: false,
    isProcessing: false,
    isPlaying: false,
    transcript: '',
    response: '',
    error: '',
    sessionId: undefined,
    languageCode: 'en-IN'
  });

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const [audioLevel, setAudioLevel] = useState(0);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animationFrameRef = useRef<number>();
  const audioElementRef = useRef<HTMLAudioElement | null>(null);

  // Check API health on component mount
  useEffect(() => {
    checkAPIHealth();
  }, []);

  const checkAPIHealth = async () => {
    try {
      const data = await apiService.checkHealth();
      console.log('✅ API Health:', data);
      setSession(prev => ({ ...prev, error: '' }));
      toast({
        title: "🚀 Connected",
        description: "Successfully connected to Sahayak AI backend",
      });
    } catch (error) {
      console.error('❌ API Health Check Failed:', error);
      setSession(prev => ({ 
        ...prev, 
        error: 'Backend connection failed. Please ensure the API server is running on port 8000.' 
      }));
      toast({
        title: "⚠️ Connection Error",
        description: "Could not connect to backend. Please start the API server.",
        variant: "destructive"
      });
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      // Set up audio analysis for visualizations
      const audioContext = new AudioContext();
      const analyser = audioContext.createAnalyser();
      const source = audioContext.createMediaStreamSource(stream);
      source.connect(analyser);
      analyser.fftSize = 256;
      analyserRef.current = analyser;

      const updateAudioLevel = () => {
        if (analyserRef.current && session.isRecording) {
          const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
          analyserRef.current.getByteFrequencyData(dataArray);
          const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
          setAudioLevel(average / 255);
          animationFrameRef.current = requestAnimationFrame(updateAudioLevel);
        }
      };

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(chunksRef.current, { type: 'audio/wav' });
        await processAudio(audioBlob);
        stream.getTracks().forEach(track => track.stop());
        if (animationFrameRef.current) {
          cancelAnimationFrame(animationFrameRef.current);
        }
        setAudioLevel(0);
      };

      mediaRecorder.start();
      setSession(prev => ({ ...prev, isRecording: true, transcript: '', response: '', error: '' }));
      updateAudioLevel();
      
      toast({
        title: "🎤 Listening...",
        description: "Speak clearly and I'll help you with your computer tasks",
      });

      // Auto-stop after 10 seconds
      setTimeout(() => {
        if (mediaRecorder.state === 'recording') {
          stopRecording();
        }
      }, 10000);

    } catch (error) {
      console.error('Error starting recording:', error);
      setSession(prev => ({ ...prev, error: 'Failed to access microphone' }));
      toast({
        title: "❌ Microphone Error",
        description: "Please check your microphone permissions and try again.",
        variant: "destructive"
      });
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
      setSession(prev => ({ ...prev, isRecording: false, isProcessing: true }));
    }
  };

  const processAudio = async (audioBlob: Blob) => {
    try {
      setSession(prev => ({ ...prev, isProcessing: true, error: '' }));

      toast({
        title: "🔄 Processing...",
        description: "Converting speech to text and executing your command",
      });

      // Call the API service
      const result = await apiService.processVoice(audioBlob, session.sessionId);
      
      // Update session with results
      setSession(prev => ({ 
        ...prev, 
        isProcessing: false,
        transcript: result.transcript,
        response: result.response_text,
        sessionId: result.agent_result?.session_id || prev.sessionId,
        languageCode: result.detected_language,
        isPlaying: true
      }));

      // Play the audio response if available
      if (result.audio_base64) {
        await playBase64Audio(result.audio_base64);
        setSession(prev => ({ ...prev, isPlaying: false }));
      } else {
        // If no audio response, just show the text and mark as not playing
        setSession(prev => ({ ...prev, isPlaying: false }));
      }

      toast({
        title: "✅ Task Completed",
        description: "Command executed successfully!",
      });
      
    } catch (error) {
      console.error('Error processing audio:', error);
      setSession(prev => ({ 
        ...prev, 
        isProcessing: false, 
        isPlaying: false,
        error: `Failed to process audio: ${error instanceof Error ? error.message : 'Unknown error'}` 
      }));
      
      toast({
        title: "❌ Processing Error",
        description: error instanceof Error ? error.message : 'Unknown error occurred',
        variant: "destructive"
      });
    }
  };



  // Cleanup function
  useEffect(() => {
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      if (audioElementRef.current) {
        audioElementRef.current.pause();
        audioElementRef.current = null;
      }
    };
  }, []);

  const getMainButtonProps = () => {
    if (session.isRecording) {
      return {
        onClick: stopRecording,
        className: "w-40 h-40 rounded-full bg-gradient-to-br from-red-500 to-pink-600 hover:from-red-600 hover:to-pink-700 text-white shadow-2xl transform hover:scale-105 transition-all duration-300 animate-pulse border-4 border-red-300",
        icon: <MicOff className="w-16 h-16" />,
        text: "Stop Recording"
      };
    } else if (session.isProcessing) {
      return {
        onClick: () => {},
        className: "w-40 h-40 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 text-white cursor-not-allowed shadow-2xl",
        icon: <div className="w-16 h-16 border-4 border-white border-t-transparent rounded-full animate-spin" />,
        text: "Processing..."
      };
    } else if (session.isPlaying) {
      return {
        onClick: () => {},
        className: "w-40 h-40 rounded-full bg-gradient-to-br from-green-500 to-emerald-600 text-white animate-pulse cursor-not-allowed shadow-2xl border-4 border-green-300",
        icon: <Play className="w-16 h-16" />,
        text: "Speaking..."
      };
    } else {
      return {
        onClick: startRecording,
        className: "w-40 h-40 rounded-full bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 hover:from-indigo-600 hover:via-purple-600 hover:to-pink-600 text-white transform hover:scale-110 transition-all duration-300 shadow-2xl hover:shadow-purple-500/25 border-4 border-white/20",
        icon: <Mic className="w-16 h-16" />,
        text: "Start Talking"
      };
    }
  };

  const buttonProps = getMainButtonProps();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 relative overflow-hidden">
      {/* Animated background elements */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-1/2 -left-1/2 w-full h-full bg-gradient-to-br from-purple-500/10 to-transparent rounded-full animate-pulse"></div>
        <div className="absolute -bottom-1/2 -right-1/2 w-full h-full bg-gradient-to-tl from-indigo-500/10 to-transparent rounded-full animate-pulse" style={{animationDelay: '2s'}}></div>
      </div>

      {/* Voice particles overlay */}
      <VoiceParticles 
        isActive={session.isRecording || session.isPlaying} 
        intensity={session.isRecording ? audioLevel : 0.5}
      />

      <div className="relative z-10 flex flex-col items-center justify-center min-h-screen p-4">
        <div className="max-w-4xl w-full space-y-8">
          {/* Header */}
          <div className="text-center space-y-6">
            <h1 className="text-6xl md:text-7xl font-bold bg-gradient-to-r from-white via-purple-200 to-indigo-200 bg-clip-text text-transparent animate-fade-in">
              Sahayak AI
            </h1>
            <p className="text-xl md:text-2xl text-gray-300 max-w-3xl mx-auto leading-relaxed">
              Your compassionate digital companion for effortless computer navigation
            </p>
            <div className="flex items-center justify-center space-x-2 text-sm text-gray-400">
              <div className={`w-2 h-2 rounded-full animate-pulse ${session.error ? 'bg-red-400' : 'bg-green-400'}`}></div>
              <span>{session.error ? 'Connection Error' : 'AI Assistant Ready'}</span>
              {session.sessionId && (
                <span className="text-xs text-purple-300">• Session: {session.sessionId.slice(0, 8)}...</span>
              )}
            </div>
          </div>

          {/* Main Voice Interface */}
          <Card className="bg-white/10 backdrop-blur-xl shadow-2xl border border-white/20 rounded-3xl overflow-hidden">
            <CardContent className="p-8 space-y-8">
              {/* Main Button with Waveform */}
              <div className="flex flex-col items-center space-y-6">
                <div className="relative">
                  <Button
                    {...buttonProps}
                    disabled={session.isProcessing || !!session.error}
                  >
                    <div className="flex flex-col items-center space-y-3">
                      {buttonProps.icon}
                      <span className="text-lg font-semibold">{buttonProps.text}</span>
                    </div>
                  </Button>
                  
                  {/* Waveform visualizer around the button */}
                  {session.isRecording && (
                    <WaveformVisualizer audioLevel={audioLevel} />
                  )}
                </div>
                
                <div className="text-center space-y-2">
                  <p className="text-white/90 text-lg max-w-md">
                    {session.isRecording && "🎤 I'm listening... Speak naturally and clearly"}
                    {session.isProcessing && "🧠 Understanding your request and preparing to help..."}
                    {session.isPlaying && "🗣️ " + (session.response.slice(0, 50) + (session.response.length > 50 ? "..." : ""))}
                    {!session.isRecording && !session.isProcessing && !session.isPlaying && !session.error && 
                      "Click the button and tell me what you'd like to do on your computer"}
                    {session.error && "❌ Please check the connection and try again"}
                  </p>
                  
                  {session.isRecording && (
                    <div className="flex items-center justify-center space-x-2 text-sm text-purple-300">
                      <div className="flex space-x-1">
                        <div className="w-1 h-4 bg-purple-400 rounded-full animate-pulse"></div>
                        <div className="w-1 h-6 bg-purple-400 rounded-full animate-pulse" style={{animationDelay: '0.1s'}}></div>
                        <div className="w-1 h-8 bg-purple-400 rounded-full animate-pulse" style={{animationDelay: '0.2s'}}></div>
                        <div className="w-1 h-6 bg-purple-400 rounded-full animate-pulse" style={{animationDelay: '0.3s'}}></div>
                        <div className="w-1 h-4 bg-purple-400 rounded-full animate-pulse" style={{animationDelay: '0.4s'}}></div>
                      </div>
                      <span>Listening...</span>
                    </div>
                  )}

                  {session.languageCode && session.languageCode !== 'en-IN' && (
                    <div className="text-sm text-blue-300">
                      🌐 Detected language: {session.languageCode}
                    </div>
                  )}
                </div>
              </div>

              {/* Status Cards */}
              <div className="grid md:grid-cols-2 gap-6">
                {/* Transcript */}
                {session.transcript && (
                  <Card className="bg-blue-500/20 border-blue-400/30 backdrop-blur-sm animate-fade-in">
                    <CardHeader>
                      <CardTitle className="text-lg text-blue-200 flex items-center gap-2">
                        <Mic className="w-5 h-5" />
                        What you said
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-blue-100 text-lg italic">"{session.transcript}"</p>
                    </CardContent>
                  </Card>
                )}

                {/* Response */}
                {session.response && (
                  <Card className="bg-green-500/20 border-green-400/30 backdrop-blur-sm animate-fade-in">
                    <CardHeader>
                      <CardTitle className="text-lg text-green-200 flex items-center gap-2">
                        <Play className="w-5 h-5" />
                        Sahayak's Response
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-green-100 text-lg">{session.response}</p>
                    </CardContent>
                  </Card>
                )}
              </div>

              {/* Error Display */}
              {session.error && (
                <Card className="bg-red-500/20 border-red-400/30 backdrop-blur-sm animate-fade-in">
                  <CardContent className="pt-6 space-y-4">
                    <p className="text-red-200 text-center text-lg">{session.error}</p>
                    <div className="flex justify-center">
                      <Button 
                        onClick={checkAPIHealth}
                        className="bg-red-600 hover:bg-red-700 text-white"
                        size="sm"
                      >
                        Retry Connection
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              )}
            </CardContent>
          </Card>

          {/* Features */}
          <div className="grid md:grid-cols-3 gap-6">
            <Card className="bg-white/10 backdrop-blur-xl border border-white/20 hover:bg-white/15 transition-all duration-300 group">
              <CardContent className="pt-6 text-center space-y-4">
                <div className="w-16 h-16 bg-gradient-to-br from-blue-400 to-blue-600 rounded-full flex items-center justify-center mx-auto group-hover:scale-110 transition-transform duration-300">
                  <Mic className="w-8 h-8 text-white" />
                </div>
                <h3 className="font-semibold text-white text-lg">Natural Speech</h3>
                <p className="text-gray-300">Speak naturally in your preferred language</p>
              </CardContent>
            </Card>

            <Card className="bg-white/10 backdrop-blur-xl border border-white/20 hover:bg-white/15 transition-all duration-300 group">
              <CardContent className="pt-6 text-center space-y-4">
                <div className="w-16 h-16 bg-gradient-to-br from-green-400 to-green-600 rounded-full flex items-center justify-center mx-auto group-hover:scale-110 transition-transform duration-300">
                  <Play className="w-8 h-8 text-white" />
                </div>
                <h3 className="font-semibold text-white text-lg">Clear Guidance</h3>
                <p className="text-gray-300">Receive spoken confirmations and helpful guidance</p>
              </CardContent>
            </Card>

            <Card className="bg-white/10 backdrop-blur-xl border border-white/20 hover:bg-white/15 transition-all duration-300 group">
              <CardContent className="pt-6 text-center space-y-4">
                <div className="w-16 h-16 bg-gradient-to-br from-purple-400 to-purple-600 rounded-full flex items-center justify-center mx-auto group-hover:scale-110 transition-transform duration-300">
                  <div className="w-8 h-8 bg-white rounded-full animate-pulse" />
                </div>
                <h3 className="font-semibold text-white text-lg">Accessible Design</h3>
                <p className="text-gray-300">Large buttons and clear visual feedback</p>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Index;
