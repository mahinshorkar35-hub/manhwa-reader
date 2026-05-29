# MangaRecap

A professional desktop application that transforms manga PDFs into narrated recap videos using AI-powered vision analysis and text-to-speech technology.

![MangaRecap Icon](resources/icon.png)

## Features

### Core Functionality
- **PDF Import**: Drag & drop or browse for manga PDF files
- **Smart Panel Detection**: Automatically detects and extracts manga panels from pages
- **AI Vision Analysis**: Analyzes panel content using advanced AI vision models
- **Story Generation**: Creates cohesive, styled narration scripts
- **Text-to-Speech**: Converts summaries into natural-sounding narration
- **Video Creation**: Combines panels and narration into polished recap videos

### Multiple AI Provider Support

| Provider | Type | Quality | Cost |
|----------|------|---------|------|
| OpenAI GPT-4o | Cloud | Best | Paid |
| OpenAI GPT-4o-mini | Cloud | Good | Lower cost |
| Google Gemini | Cloud | Good | Free tier available |
| Ollama (Local) | Local | Varies | Free |

### Multiple TTS (Voice) Support

| Provider | Type | Quality | Cost |
|----------|------|---------|------|
| Microsoft Edge TTS | Cloud | Good | Free |
| Kokoro TTS | Local | Excellent | Free |
| ElevenLabs | Cloud | Best | Paid |
| System TTS | Local | Basic | Free |

### Professional GUI
- Modern dark/light theme with smooth animations
- Drag-and-drop PDF import
- Real-time progress tracking with detailed logs
- Library view with thumbnails and playback
- Secure encrypted API key storage
- Responsive design that doesn't freeze during processing

## Installation

### Method 1: Pre-built Executable (Recommended)

1. Download the latest release from the [Releases](https://github.com/yourusername/manga-recap/releases) page
2. Extract the ZIP file
3. Run `MangaRecap.exe`

### Method 2: Build from Source

#### Prerequisites
- Python 3.11 or higher
- Windows 10/11
- (Optional) FFmpeg for video encoding

#### Setup Steps

```bash
# Clone the repository
git clone https://github.com/yourusername/manga-recap.git
cd manga-recap

# Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

#### Building the Executable

```bash
# Method A: Folder-based build (recommended - faster startup)
build.bat

# Method B: Single-file build (slower startup, more portable)
pyinstaller build_onefile.spec --clean --noconfirm
```

The built executable will be in the `dist/MangaRecap` folder.

## Usage Guide

### First-Time Setup

1. Launch MangaRecap
2. Go to **Settings** (gear icon in sidebar)
3. Add your API keys:
   - **OpenAI API Key** (for GPT-4o vision): Get from [platform.openai.com](https://platform.openai.com)
   - **Gemini API Key** (alternative): Get from [aistudio.google.com](https://aistudio.google.com)
   - **ElevenLabs API Key** (optional, for premium voices): Get from [elevenlabs.io](https://elevenlabs.io)
4. Configure output folder (optional)
5. Click **Save Settings**

### Creating Your First Recap

1. Click **New Project** in the sidebar
2. Drag & drop a manga PDF onto the drop zone, or click **Browse**
3. The app will auto-detect the title and volume number
4. Adjust processing options:
   - **AI Vision**: Select your preferred AI provider
   - **Panel Detection**: Medium is recommended for most manga
   - **Narration Style**: Choose your preferred storytelling tone
   - **Voice**: Select a TTS provider and voice
5. Click **Start Processing**
6. Watch real-time progress as the app:
   - Extracts pages from the PDF
   - Detects and crops panels
   - Analyzes panels with AI vision
   - Generates a story summary
   - Creates narration audio
   - Renders the final video
7. Click **Play** when complete!

### Using Free Options Only

You can use MangaRecap completely free:

1. **AI Vision**: Select **Ollama (Local)** in settings
   - Install [Ollama](https://ollama.com) on your computer
   - Run: `ollama pull llava` to download a vision model
   - Start Ollama: `ollama serve`

2. **Voice**: Select **Microsoft Edge TTS** or **Kokoro TTS**
   - Edge TTS works immediately (no setup)
   - For Kokoro: `pip install kokoro soundfile`

### Narration Styles

| Style | Description | Best For |
|-------|-------------|----------|
| Dramatic | Epic, vivid storytelling with emotional intensity | Action manga |
| Casual | Friendly, conversational tone | Slice of life |
| Anime Style | Enthusiastic anime-fan energy | All genres |
| Concise | Brief, to-the-point summary | Quick recaps |

## Project Structure

```
manga-recap/
├── core/                       # Core processing modules
│   ├── __init__.py
│   ├── manga_extraction.py     # PDF extraction & panel detection
│   ├── vision_analysis.py      # AI vision analysis
│   ├── narration.py            # Text-to-speech generation
│   ├── movie_director.py       # Video creation & rendering
│   ├── config_manager.py       # Settings & encrypted key storage
│   └── worker.py               # Background processing thread
├── gui/                        # User interface
│   ├── __init__.py
│   ├── styles.py               # Theme system
│   ├── main_window.py          # Main application window
│   ├── new_project_page.py     # Processing page
│   ├── library_page.py         # History/library page
│   └── settings_page.py        # Settings page
├── resources/                  # App assets
│   ├── icon.png                # Application icon (PNG)
│   └── icon.ico                # Application icon (ICO)
├── main.py                     # Application entry point
├── requirements.txt            # Python dependencies
├── manga_recap.spec            # PyInstaller spec (folder mode)
├── build_onefile.spec          # PyInstaller spec (single file)
├── build.bat                   # Windows build script
└── README.md                   # This file
```

## Configuration

Settings are stored encrypted in your user data folder:
- Windows: `%APPDATA%\MangaRecap\`
- Config: `settings.json` (API keys are encrypted)
- History: `history.json`
- Logs: `logs/manga_recap.log`

## Troubleshooting

### Common Issues

**"OpenAI API key not configured"**
- Go to Settings and add your OpenAI API key
- Or switch to a free provider (Ollama/Gemini)

**"Ollama connection error"**
- Make sure Ollama is running: `ollama serve`
- Verify the URL in Settings matches your Ollama instance

**"Video has no audio"**
- Install FFmpeg and add it to your PATH
- Or switch to a different TTS provider

**"Processing is slow"**
- Use GPT-4o-mini instead of GPT-4o
- Set panel detection to "Low"
- Reduce max panels to 10-15

**"App freezes during processing"**
- This shouldn't happen - processing runs in a background thread
- Check the log for errors: `%APPDATA%\MangaRecap\logs\manga_recap.log`

### Getting API Keys

**OpenAI:**
1. Visit [platform.openai.com](https://platform.openai.com)
2. Sign up or log in
3. Go to API Keys section
4. Create a new key

**Google Gemini:**
1. Visit [aistudio.google.com](https://aistudio.google.com)
2. Sign in with Google
3. Get API key from settings

**ElevenLabs (optional):**
1. Visit [elevenlabs.io](https://elevenlabs.io)
2. Sign up (free tier available)
3. Get API key from profile settings

## Development

### Adding New AI Providers

1. Create a new class in `core/vision_analysis.py` inheriting from `BaseVisionProvider`
2. Implement `analyze_image()`, `analyze_panel()`, and `analyze_panels_batch()`
3. Add to `VisionAnalyzer.PROVIDERS` dict
4. Add UI option in `gui/new_project_page.py`

### Adding New TTS Providers

1. Create a new class in `core/narration.py` inheriting from `BaseTTSProvider`
2. Implement `generate_audio()` and `get_voices()`
3. Add to `NarrationGenerator.PROVIDERS` dict
4. Add UI option in `gui/new_project_page.py`

## License

This project is licensed under the MIT License - see LICENSE file for details.

## Acknowledgments

- Original concept inspired by [pashpashpash/manga-reader](https://github.com/pashpashpash/manga-reader)
- Built with PyQt6 for the professional GUI
- Uses OpenAI GPT-4o for vision analysis
- Uses multiple open-source TTS engines for voice generation
