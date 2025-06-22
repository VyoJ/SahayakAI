# Sahayak AI - Voice-Controlled Computer Interface

A modern, accessible voice interface that allows users to control their computers through natural speech. Built with React + TypeScript frontend and FastAPI backend, powered by Sarvam AI for speech recognition and synthesis.

## ✨ Features

- **🎤 Natural Speech Recognition** - Speak naturally in multiple languages
- **🤖 Intelligent Computer Control** - Execute computer tasks through voice commands
- **🗣️ Text-to-Speech Responses** - Get audio confirmations and guidance
- **🎯 Session Management** - Continuous conversation context
- **♿ Accessible Design** - Large buttons and clear visual feedback
- **🌐 Multi-language Support** - Automatic language detection

## 🏗️ Architecture

- **Frontend**: React + TypeScript + Vite + Tailwind CSS + shadcn/ui
- **Backend**: FastAPI + Python
- **AI Services**: Sarvam AI for ASR and TTS
- **Computer Control**: Custom computer use agent

## 🚀 Quick Start

### Prerequisites

- **Node.js** (v18 or later)
- **Python** (v3.8 or later)
- **Sarvam AI API Key** (sign up at [sarvam.ai](https://sarvam.ai))

### Installation

1. **Clone and setup the project:**
```bash
git clone <repository-url>
cd digital-ease-voice-bridge
```

2. **Install frontend dependencies:**
```bash
npm install
```

3. **Install backend dependencies:**
```bash
npm run install:backend
# or manually:
pip install fastapi uvicorn python-multipart requests pyaudio pygame
```

4. **Configure API Key:**
   - Update `fastapi_backend.py` line 25 with your Sarvam API key:
   ```python
   API_KEY = "your_sarvam_api_key_here"
   ```

### Running the Application

#### Option 1: Run both services simultaneously (Recommended)
```bash
npm run start:all
```

#### Option 2: Run services separately

**Terminal 1 - Backend:**
```bash
npm run backend:uvicorn
# or
uvicorn fastapi_backend:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
npm run dev
```

### Access the Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 🎯 Usage

1. **Start the Application** using one of the methods above
2. **Click the microphone button** to start recording
3. **Speak your command** clearly (e.g., "Open calculator", "Take a screenshot")
4. **Wait for processing** - the AI will transcribe, execute, and respond
5. **Listen to the response** - audio confirmation will play automatically

### Example Voice Commands

- "Open calculator application"
- "Take a screenshot"
- "Open file explorer"
- "Close the current window"
- "Search for something on Google"

## 🛠️ API Endpoints

### Core Endpoints

- `POST /process-voice` - Complete voice processing pipeline
- `POST /text-to-speech` - Convert text to speech
- `POST /speech-to-text` - Convert speech to text only
- `GET /health` - API health check

### Session Management

- `GET /sessions/{session_id}` - Get session info
- `DELETE /sessions/{session_id}` - Delete session

## 🏁 Development

### Project Structure

```
digital-ease-voice-bridge/
├── src/                    # Frontend source code
│   ├── components/         # React components
│   ├── lib/               # Utilities and API service
│   ├── pages/             # Main application pages
│   └── hooks/             # Custom React hooks
├── fastapi_backend.py     # Backend API server
├── voice_interface.py     # Voice processing logic
└── computer_use_agent/    # Computer control agent
```

### Frontend Development

```bash
npm run dev          # Start development server
npm run build        # Build for production
npm run lint         # Run linter
```

### Backend Development

```bash
npm run backend:uvicorn  # Start backend with auto-reload
python fastapi_backend.py  # Direct Python execution
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file for configuration:

```env
SARVAM_API_KEY=your_api_key_here
API_BASE_URL=http://localhost:8000
FRONTEND_URL=http://localhost:5173
```

### API Configuration

Update `src/lib/api.ts` to change the API base URL:

```typescript
const API_BASE_URL = 'http://localhost:8000';
```

## 🐛 Troubleshooting

### Common Issues

**1. Microphone not working**
- Check browser permissions for microphone access
- Ensure you're using HTTPS or localhost
- Try refreshing the page

**2. Backend connection failed**
- Ensure the FastAPI server is running on port 8000
- Check if the API key is configured correctly
- Verify Python dependencies are installed

**3. Audio playback issues**
- Check browser audio permissions
- Ensure speakers/headphones are connected
- Try using a different browser

**4. Voice commands not working**
- Speak clearly and at normal pace
- Ensure good microphone quality
- Check internet connection for API calls

### Debug Mode

Enable debug logging in the browser console to see detailed API interactions.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Sarvam AI](https://sarvam.ai) for speech recognition and synthesis
- [FastAPI](https://fastapi.tiangolo.com/) for the robust backend framework
- [React](https://reactjs.org/) and [Vite](https://vitejs.dev/) for the frontend
- [shadcn/ui](https://ui.shadcn.com/) for beautiful UI components

## 📞 Support

For support, please:
1. Check the troubleshooting section above
2. Search existing issues on GitHub
3. Create a new issue with detailed information

---

**Made with ❤️ for accessible computing**
