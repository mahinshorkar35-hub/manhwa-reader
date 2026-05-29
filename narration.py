"""
Narration Module
Generates audio narration from text summaries.
Supports ElevenLabs API and free local TTS options (Kokoro, pyttsx3, edge-tts).
"""

import os
import re
import json
import logging
import tempfile
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Callable
from dataclasses import dataclass
import requests

logger = logging.getLogger(__name__)


@dataclass
class NarrationSegment:
    """A segment of narration with timing info."""
    text: str
    audio_path: str
    duration: float
    panel_index: int


class BaseTTSProvider:
    """Base class for TTS providers."""

    def generate_audio(self, text: str, output_path: str, voice_id: Optional[str] = None) -> float:
        """Generate audio from text. Returns duration in seconds."""
        raise NotImplementedError

    def get_voices(self) -> List[Dict]:
        """Get available voices."""
        return []


class ElevenLabsProvider(BaseTTSProvider):
    """ElevenLabs TTS API provider with high-quality voices."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.elevenlabs.io/v1"
        self.headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json"
        }

    def get_voices(self) -> List[Dict]:
        """Fetch available voices from ElevenLabs."""
        try:
            response = requests.get(f"{self.base_url}/voices", headers=self.headers, timeout=30)
            response.raise_for_status()
            voices = response.json().get('voices', [])
            return [
                {
                    'id': v['voice_id'],
                    'name': v['name'],
                    'preview_url': v.get('preview_url', ''),
                    'category': v.get('category', 'premade')
                }
                for v in voices
            ]
        except Exception as e:
            logger.error(f"Failed to fetch ElevenLabs voices: {e}")
            # Return default voices
            return [
                {'id': '21m00Tcm4TlvDq8ikWAM', 'name': 'Rachel', 'category': 'premade'},
                {'id': 'AZnzlk1XvdvUeBnXmlld', 'name': 'Domi', 'category': 'premade'},
                {'id': 'EXAVITQu4vr4xnSDxMaL', 'name': 'Bella', 'category': 'premade'},
                {'id': 'ErXwobaYiN019PkySvjV', 'name': 'Antoni', 'category': 'premade'},
                {'id': 'MF3mGyEYCl7XYWbV9V6O', 'name': 'Elli', 'category': 'premade'},
                {'id': 'TxGEqnHWrfWFTfGW9XjX', 'name': 'Josh', 'category': 'premade'},
                {'id': 'VR6AewLTigWG4xSOukaG', 'name': 'Arnold', 'category': 'premade'},
                {'id': 'pNInz6obpgDQGcFmaJgB', 'name': 'Adam', 'category': 'premade'},
                {'id': 'yoZ06aMxZJJ28mfd3POQ', 'name': 'Sam', 'category': 'premade'},
            ]

    def generate_audio(self, text: str, output_path: str, voice_id: Optional[str] = None) -> float:
        """Generate audio using ElevenLabs API."""
        voice_id = voice_id or "21m00Tcm4TlvDq8ikWAM"

        try:
            url = f"{self.base_url}/text-to-speech/{voice_id}"

            payload = {
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                    "style": 0.0,
                    "use_speaker_boost": True
                }
            }

            response = requests.post(url, json=payload, headers=self.headers, timeout=120)
            response.raise_for_status()

            with open(output_path, 'wb') as f:
                f.write(response.content)

            # Estimate duration (rough approximation)
            word_count = len(text.split())
            duration = word_count * 0.5  # ~0.5s per word average

            logger.info(f"Generated ElevenLabs audio: {output_path} ({duration:.1f}s)")
            return duration

        except Exception as e:
            logger.error(f"ElevenLabs TTS failed: {e}")
            raise


class EdgeTTSProvider(BaseTTSProvider):
    """
    Microsoft Edge TTS provider (free, no API key needed).
    Requires edge-tts Python package: pip install edge-tts
    """

    def __init__(self):
        self.base_url = "https://speech.platform.bing.com/consumer/speech/synthesize/readaloud"
        self.voices_list = [
            {'id': 'en-US-AriaNeural', 'name': 'Aria (US Female)', 'gender': 'Female'},
            {'id': 'en-US-GuyNeural', 'name': 'Guy (US Male)', 'gender': 'Male'},
            {'id': 'en-US-JennyNeural', 'name': 'Jenny (US Female)', 'gender': 'Female'},
            {'id': 'en-GB-SoniaNeural', 'name': 'Sonia (UK Female)', 'gender': 'Female'},
            {'id': 'en-GB-RyanNeural', 'name': 'Ryan (UK Male)', 'gender': 'Male'},
            {'id': 'ja-JP-NanamiNeural', 'name': 'Nanami (Japanese Female)', 'gender': 'Female'},
            {'id': 'ja-JP-KeitaNeural', 'name': 'Keita (Japanese Male)', 'gender': 'Male'},
        ]

    def get_voices(self) -> List[Dict]:
        return self.voices_list

    def generate_audio(self, text: str, output_path: str, voice_id: Optional[str] = None) -> float:
        """Generate audio using edge-tts library."""
        voice_id = voice_id or "en-US-AriaNeural"

        try:
            import edge_tts
            import asyncio

            async def _generate():
                communicate = edge_tts.Communicate(text, voice_id)
                await communicate.save(output_path)

            asyncio.run(_generate())

            # Estimate duration
            word_count = len(text.split())
            duration = word_count * 0.5

            logger.info(f"Generated Edge TTS audio: {output_path} ({duration:.1f}s)")
            return duration

        except ImportError:
            raise ImportError("edge-tts not installed. Run: pip install edge-tts")
        except Exception as e:
            logger.error(f"Edge TTS failed: {e}")
            raise


class KokoroTTSProvider(BaseTTSProvider):
    """
    Kokoro TTS provider (free, high-quality local TTS).
    Requires kokoro Python package: pip install kokoro
    Supports multiple languages with various voices.
    """

    def __init__(self, lang_code: str = "a"):
        """
        Initialize Kokoro TTS.

        Args:
            lang_code: Language code - "a" (American English), "b" (British),
                      "j" (Japanese), "z" (Mandarin), etc.
        """
        self.lang_code = lang_code
        self._pipeline = None
        self.voices_list = [
            {'id': 'af', 'name': 'American Female (Bella+Sarah)', 'lang': 'a'},
            {'id': 'af_bella', 'name': 'Bella (American Female)', 'lang': 'a'},
            {'id': 'af_sarah', 'name': 'Sarah (American Female)', 'lang': 'a'},
            {'id': 'am_adam', 'name': 'Adam (American Male)', 'lang': 'a'},
            {'id': 'am_michael', 'name': 'Michael (American Male)', 'lang': 'a'},
            {'id': 'bf_emma', 'name': 'Emma (British Female)', 'lang': 'b'},
            {'id': 'bf_isabella', 'name': 'Isabella (British Female)', 'lang': 'b'},
            {'id': 'bm_george', 'name': 'George (British Male)', 'lang': 'b'},
            {'id': 'bm_lewis', 'name': 'Lewis (British Male)', 'lang': 'b'},
        ]

    def _get_pipeline(self):
        """Lazy load the Kokoro pipeline."""
        if self._pipeline is None:
            try:
                from kokoro import KPipeline
                self._pipeline = KPipeline(lang_code=self.lang_code)
                logger.info(f"Initialized Kokoro TTS pipeline with lang: {self.lang_code}")
            except ImportError:
                raise ImportError("kokoro not installed. Run: pip install kokoro")
        return self._pipeline

    def get_voices(self) -> List[Dict]:
        return self.voices_list

    def generate_audio(self, text: str, output_path: str, voice_id: Optional[str] = None) -> float:
        """Generate audio using Kokoro TTS."""
        voice_id = voice_id or "af_bella"

        try:
            pipeline = self._get_pipeline()

            # Split text into sentences for better processing
            sentences = self._split_into_sentences(text)

            import soundfile as sf
            all_audio = []

            generator = pipeline(sentences, voice=voice_id, speed=1.0, split_pattern=r'[.!?]+')

            for i, (gs, ps, audio) in enumerate(generator):
                all_audio.append(audio)

            # Concatenate all audio segments
            if all_audio:
                import numpy as np
                combined = np.concatenate(all_audio)
                sf.write(output_path, combined, 24000)

                # Calculate duration
                duration = len(combined) / 24000
                logger.info(f"Generated Kokoro audio: {output_path} ({duration:.1f}s)")
                return duration
            else:
                raise RuntimeError("No audio generated")

        except ImportError as e:
            raise ImportError(f"Required package missing: {e}")
        except Exception as e:
            logger.error(f"Kokoro TTS failed: {e}")
            raise

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences for processing."""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]


class Pyttsx3Provider(BaseTTSProvider):
    """
    pyttsx3 provider (completely free, offline, uses system TTS).
    Lower quality but requires no installation or API keys.
    """

    def __init__(self):
        self._engine = None
        self.voices_list = []
        self._init_voices()

    def _get_engine(self):
        """Lazy initialize pyttsx3 engine."""
        if self._engine is None:
            try:
                import pyttsx3
                self._engine = pyttsx3.init()
                self._engine.setProperty('rate', 175)
                self._engine.setProperty('volume', 0.9)
            except ImportError:
                raise ImportError("pyttsx3 not installed. Run: pip install pyttsx3")
        return self._engine

    def _init_voices(self):
        """Initialize available voices."""
        try:
            engine = self._get_engine()
            voices = engine.getProperty('voices')
            self.voices_list = [
                {'id': str(i), 'name': v.name, 'lang': getattr(v, 'languages', ['en'])[0] if hasattr(v, 'languages') else 'en'}
                for i, v in enumerate(voices)
            ]
        except Exception as e:
            logger.warning(f"Could not load pyttsx3 voices: {e}")
            self.voices_list = [{'id': '0', 'name': 'Default Voice', 'lang': 'en'}]

    def get_voices(self) -> List[Dict]:
        return self.voices_list

    def generate_audio(self, text: str, output_path: str, voice_id: Optional[str] = None) -> float:
        """Generate audio using pyttsx3."""
        try:
            engine = self._get_engine()

            if voice_id:
                voices = engine.getProperty('voices')
                vid = int(voice_id)
                if vid < len(voices):
                    engine.setProperty('voice', voices[vid].id)

            engine.save_to_file(text, output_path)
            engine.runAndWait()

            # Estimate duration
            word_count = len(text.split())
            duration = word_count * 0.5

            logger.info(f"Generated pyttsx3 audio: {output_path} ({duration:.1f}s)")
            return duration

        except Exception as e:
            logger.error(f"pyttsx3 TTS failed: {e}")
            raise


class NarrationGenerator:
    """Main narration orchestrator."""

    PROVIDERS = {
        'elevenlabs': ElevenLabsProvider,
        'edge': EdgeTTSProvider,
        'kokoro': KokoroTTSProvider,
        'pyttsx3': Pyttsx3Provider,
    }

    def __init__(self, provider_name: str = 'edge', **kwargs):
        """
        Initialize the narration generator.

        Args:
            provider_name: One of 'elevenlabs', 'edge', 'kokoro', 'pyttsx3'
            **kwargs: Provider-specific arguments
        """
        provider_class = self.PROVIDERS.get(provider_name.lower())
        if not provider_class:
            raise ValueError(f"Unknown provider: {provider_name}. Available: {list(self.PROVIDERS.keys())}")

        self.provider = provider_class(**kwargs)
        self.provider_name = provider_name
        logger.info(f"Initialized narration generator with provider: {provider_name}")

    def get_available_voices(self) -> List[Dict]:
        """Get list of available voices."""
        return self.provider.get_voices()

    def generate_full_narration(
        self,
        summary: str,
        output_dir: str,
        voice_id: Optional[str] = None,
        progress_callback: Optional[Callable[[str, int], None]] = None
    ) -> str:
        """
        Generate narration audio from a story summary.

        Args:
            summary: The story summary text
            output_dir: Directory to save audio files
            voice_id: Voice ID to use
            progress_callback: Progress callback

        Returns:
            Path to the generated narration audio file
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Clean the summary text for narration
        clean_text = self._prepare_text_for_narration(summary)

        output_path = output_dir / "narration.mp3"

        if progress_callback:
            progress_callback("Generating narration audio...", 0)

        try:
            duration = self.provider.generate_audio(clean_text, str(output_path), voice_id)

            if progress_callback:
                progress_callback("Narration complete", 100)

            logger.info(f"Generated narration: {output_path} ({duration:.1f}s)")
            return str(output_path)

        except Exception as e:
            logger.error(f"Narration generation failed: {e}")
            raise

    def generate_timed_segments(
        self,
        summary: str,
        panel_analyses: List,
        output_dir: str,
        voice_id: Optional[str] = None,
        progress_callback: Optional[Callable[[str, int], None]] = None
    ) -> List[NarrationSegment]:
        """
        Generate narration broken into segments aligned with panels.

        Args:
            summary: Story summary
            panel_analyses: Panel analysis results
            output_dir: Output directory
            voice_id: Voice ID
            progress_callback: Progress callback

        Returns:
            List of narration segments
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Split summary into segments based on panels
        segments_text = self._split_summary_by_panels(summary, len(panel_analyses))

        segments = []
        total = len(segments_text)

        for i, (text, panel) in enumerate(zip(segments_text, panel_analyses)):
            seg_path = output_dir / f"narration_segment_{i:03d}.mp3"

            try:
                duration = self.provider.generate_audio(text, str(seg_path), voice_id)
                segment = NarrationSegment(
                    text=text,
                    audio_path=str(seg_path),
                    duration=duration,
                    panel_index=i
                )
                segments.append(segment)

                if progress_callback:
                    progress_callback(f"Generating segment {i+1}/{total}", int((i+1)/total*100))

            except Exception as e:
                logger.error(f"Failed to generate segment {i}: {e}")

        return segments

    def _prepare_text_for_narration(self, text: str) -> str:
        """Clean and prepare text for TTS narration."""
        # Remove markdown formatting
        text = re.sub(r'[#*_`]', '', text)
        # Remove extra whitespace
        text = ' '.join(text.split())
        # Replace newlines with periods for better flow
        text = text.replace('\n', '. ')
        # Clean up multiple periods
        text = re.sub(r'\.+', '. ', text)
        return text.strip()

    def _split_summary_by_panels(self, summary: str, num_panels: int) -> List[str]:
        """Split a summary into segments for each panel."""
        # Split by sentences
        sentences = re.split(r'(?<=[.!?])\s+', summary)
        sentences = [s.strip() for s in sentences if s.strip()]

        if not sentences:
            return [summary]

        # Distribute sentences across panels
        segments = []
        sentences_per_panel = max(1, len(sentences) // num_panels)

        for i in range(num_panels):
            start = i * sentences_per_panel
            end = start + sentences_per_panel if i < num_panels - 1 else len(sentences)
            segment_text = ' '.join(sentences[start:end])
            if segment_text:
                segments.append(segment_text)

        return segments

    def estimate_duration(self, text: str) -> float:
        """Estimate narration duration in seconds."""
        word_count = len(text.split())
        # Average speaking rate: ~150 words per minute = 2.5 words per second
        return word_count / 2.5
