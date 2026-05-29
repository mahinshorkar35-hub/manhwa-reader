"""
Processing Worker Module
Handles manga processing in a background thread with progress reporting.
"""

import os
import json
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List
from dataclasses import dataclass, asdict

from PyQt6.QtCore import QThread, pyqtSignal

from core.manga_extraction import MangaExtractor
from core.vision_analysis import VisionAnalyzer
from core.narration import NarrationGenerator
from core.movie_director import MovieDirector, VideoConfig
from core.config_manager import ConfigManager

logger = logging.getLogger(__name__)


@dataclass
class ProcessingResult:
    """Result of a processing job."""
    success: bool
    video_path: str = ""
    title: str = ""
    volume: str = ""
    total_panels: int = 0
    selected_panels: int = 0
    narration_duration: float = 0.0
    video_duration: float = 0.0
    error_message: str = ""
    created_at: str = ""
    thumbnail_path: str = ""
    manga_title: str = ""
    output_dir: str = ""


class ProcessingWorker(QThread):
    """Background worker for manga processing."""

    # Signals
    progress_updated = pyqtSignal(str, int)  # message, percentage
    step_changed = pyqtSignal(str)  # current step name
    log_message = pyqtSignal(str)  # log line
    processing_complete = pyqtSignal(object)  # ProcessingResult
    processing_cancelled = pyqtSignal()

    def __init__(
        self,
        pdf_path: str,
        config_manager: ConfigManager,
        options: Dict,
        parent=None
    ):
        super().__init__(parent)
        self.pdf_path = pdf_path
        self.config = config_manager
        self.options = options
        self._cancelled = False

        # Processing components
        self.extractor: Optional[MangaExtractor] = None
        self.analyzer: Optional[VisionAnalyzer] = None
        self.narrator: Optional[NarrationGenerator] = None
        self.director: Optional[MovieDirector] = None

    def cancel(self):
        """Request cancellation of processing."""
        self._cancelled = True
        self.log_message.emit("Cancellation requested...")

    def is_cancelled(self) -> bool:
        """Check if processing was cancelled."""
        return self._cancelled

    def _check_cancelled(self):
        """Raise exception if cancelled."""
        if self._cancelled:
            raise InterruptedError("Processing cancelled by user")

    def _emit_progress(self, message: str, percent: int):
        """Emit progress update."""
        self.progress_updated.emit(message, percent)
        self.log_message.emit(f"[{percent}%] {message}")

    def _emit_step(self, step_name: str):
        """Emit step change."""
        self.step_changed.emit(step_name)
        self.log_message.emit(f">>> {step_name}")

    def run(self):
        """Main processing workflow."""
        result = ProcessingResult(
            success=False,
            title=self.options.get('title', ''),
            volume=self.options.get('volume', ''),
            manga_title=self.options.get('title', ''),
            created_at=datetime.now().isoformat()
        )

        temp_dirs = []

        try:
            self._check_cancelled()

            # Setup directories
            work_dir = Path(self.config.get_temp_dir()) / f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            work_dir.mkdir(parents=True, exist_ok=True)
            temp_dirs.append(str(work_dir))

            output_dir = Path(self.options.get('output_dir', self.config.get_output_dir()))
            output_dir.mkdir(parents=True, exist_ok=True)
            result.output_dir = str(output_dir)

            # Step 1: Extract pages from PDF
            self._emit_step("Extracting Pages")
            self._emit_progress("Opening PDF and extracting pages...", 0)

            extraction_level = self.options.get('extraction_level', 'medium')
            self.extractor = MangaExtractor(extraction_level=extraction_level)

            pages_dir = work_dir / "pages"
            page_images = self.extractor.extract_pages(
                self.pdf_path,
                str(pages_dir),
                progress_callback=lambda msg, p: self._emit_progress(msg, p * 0.15)
            )

            self._emit_progress(f"Extracted {len(page_images)} pages", 15)
            self._check_cancelled()

            # Step 2: Detect panels
            self._emit_step("Detecting Panels")
            self._emit_progress("Analyzing page layouts for panels...", 15)

            panels_dir = work_dir / "panels"
            all_panels = self.extractor.extract_all_panels(
                page_images,
                str(panels_dir),
                progress_callback=lambda msg, p: self._emit_progress(msg, 15 + p * 0.10)
            )

            # Flatten panel list
            flat_panels = []
            for page_panels in all_panels:
                flat_panels.extend(page_panels)

            result.total_panels = len(flat_panels)
            self._emit_progress(f"Found {len(flat_panels)} panels", 25)
            self._check_cancelled()

            if not flat_panels:
                raise ValueError("No panels detected. The PDF may not contain manga content.")

            # Step 3: Vision Analysis
            self._emit_step("Analyzing with AI Vision")
            self._emit_progress("Setting up vision analyzer...", 25)

            vision_provider = self.options.get('vision_provider', 'openai')
            provider_kwargs = {}

            if vision_provider == 'openai':
                api_key = self.config.get_api_key('openai')
                if not api_key:
                    raise ValueError("OpenAI API key not configured. Please add it in Settings.")
                provider_kwargs = {
                    'api_key': api_key,
                    'model': self.options.get('vision_model', 'gpt-4o')
                }
            elif vision_provider == 'gemini':
                api_key = self.config.get_api_key('gemini')
                if not api_key:
                    raise ValueError("Gemini API key not configured. Please add it in Settings.")
                provider_kwargs = {'api_key': api_key}
            elif vision_provider == 'ollama':
                provider_kwargs = {
                    'model': self.config.get('ollama_model', 'llava'),
                    'base_url': self.config.get('ollama_url', 'http://localhost:11434')
                }

            self.analyzer = VisionAnalyzer(vision_provider, **provider_kwargs)

            # Get panel image paths
            panel_paths = [p['image_path'] for p in flat_panels if p.get('image_path')]

            self._emit_progress("AI is analyzing each panel (this may take a while)...", 26)
            panel_analyses = self.analyzer.analyze_panels_batch(
                panel_paths,
                progress_callback=lambda msg, p: self._emit_progress(msg, 26 + p * 0.30)
            )

            self._emit_progress(f"Analyzed {len(panel_analyses)} panels", 56)
            self._check_cancelled()

            # Step 4: Select key panels
            self._emit_step("Selecting Key Panels")
            self._emit_progress("Choosing the most important panels...", 56)

            max_panels = self.options.get('max_panels', 20)
            selected = self.analyzer.select_key_panels(panel_analyses, max_panels)

            selected_indices = [idx for idx, _ in selected]
            selected_panels = [flat_panels[idx] for idx in selected_indices]
            selected_analyses = [analysis for _, analysis in selected]
            result.selected_panels = len(selected_panels)

            self._emit_progress(f"Selected {len(selected_panels)} key panels", 58)
            self._check_cancelled()

            # Step 5: Generate story summary
            self._emit_step("Generating Story Summary")
            self._emit_progress("Creating narration script...", 58)

            summary = self.analyzer.generate_story_summary(
                selected_analyses,
                style=self.options.get('summary_style', 'dramatic'),
                title=self.options.get('title', ''),
                volume=self.options.get('volume', '')
            )

            # Save summary to file
            summary_path = work_dir / "summary.txt"
            summary_path.write_text(summary)

            self._emit_progress("Story summary complete", 60)
            self._check_cancelled()

            # Step 6: Generate narration
            self._emit_step("Generating Narration")
            self._emit_progress("Converting story to speech...", 60)

            tts_provider = self.options.get('tts_provider', 'edge')
            tts_kwargs = {}

            if tts_provider == 'elevenlabs':
                api_key = self.config.get_api_key('elevenlabs')
                if not api_key:
                    raise ValueError("ElevenLabs API key not configured. Please add it in Settings.")
                tts_kwargs = {'api_key': api_key}
            elif tts_provider == 'kokoro':
                tts_kwargs = {'lang_code': 'a'}

            self.narrator = NarrationGenerator(tts_provider, **tts_kwargs)

            narration_audio = self.narrator.generate_full_narration(
                summary,
                str(work_dir),
                voice_id=self.options.get('tts_voice', ''),
                progress_callback=lambda msg, p: self._emit_progress(msg, 60 + p * 0.15)
            )

            result.narration_duration = self.narrator.estimate_duration(summary)
            self._emit_progress("Narration generated", 75)
            self._check_cancelled()

            # Step 7: Create video
            self._emit_step("Rendering Video")
            self._emit_progress("Creating recap video with panels and narration...", 75)

            # Build video config
            resolution = self.options.get('video_resolution', '720p')
            width, height = 1280, 720
            if resolution == '1080p':
                width, height = 1920, 1080

            video_config = VideoConfig(
                width=width,
                height=height,
                fps=self.config.get('video_fps', 24),
                bitrate=self.config.get('video_bitrate', '5000k'),
                ken_burns=self.options.get('ken_burns', True),
                text_overlay=self.options.get('text_overlay', True)
            )
            self.director = MovieDirector(video_config)

            # Get selected panel image paths
            selected_panel_paths = [p['image_path'] for p in selected_panels if p.get('image_path')]

            # Generate chapter titles
            chapter_titles = []
            if self.options.get('include_chapter_titles', True):
                for i, analysis in enumerate(selected_analyses):
                    if analysis.action:
                        chapter_titles.append(f"Scene {i+1}: {analysis.action}")
                    else:
                        chapter_titles.append(f"Scene {i+1}")

            # Generate output filename
            safe_title = "".join(c for c in result.title if c.isalnum() or c in ' -_').strip()
            if not safe_title:
                safe_title = "manga_recap"
            output_filename = f"{safe_title}_Vol{result.volume}_recap.mp4"
            video_output_path = str(output_dir / output_filename)

            # Create video
            final_video = self.director.create_recap_video(
                panel_paths=selected_panel_paths,
                narration_audio_path=narration_audio,
                output_path=video_output_path,
                title=f"{result.title} - Vol. {result.volume}",
                chapter_titles=chapter_titles,
                transition_type=self.options.get('transition_type', 'fade'),
                progress_callback=lambda msg, p: self._emit_progress(msg, 75 + p * 0.25)
            )

            result.video_path = final_video
            result.video_duration = self.director.estimate_video_duration(
                len(selected_panel_paths), result.narration_duration
            )

            # Generate thumbnail
            if selected_panel_paths:
                thumb_path = output_dir / f"{safe_title}_Vol{result.volume}_thumbnail.jpg"
                self._generate_thumbnail(selected_panel_paths[0], str(thumb_path))
                result.thumbnail_path = str(thumb_path)

            self._emit_progress("Video rendering complete!", 100)

            # Save to history
            self._save_to_history(result)

            # Cleanup temp files
            if not self.config.get('preserve_temp_files', False):
                self._cleanup_temp_dirs(temp_dirs)

            result.success = True
            self.processing_complete.emit(result)

        except InterruptedError:
            self.log_message.emit("Processing cancelled.")
            self._cleanup_temp_dirs(temp_dirs)
            self.processing_cancelled.emit()

        except Exception as e:
            logger.exception("Processing failed")
            result.error_message = str(e)
            self._emit_progress(f"Error: {e}", 0)
            self._cleanup_temp_dirs(temp_dirs)
            self.processing_complete.emit(result)

    def _generate_thumbnail(self, panel_path: str, output_path: str):
        """Generate a thumbnail from the first panel."""
        try:
            from PIL import Image
            img = Image.open(panel_path)
            img.thumbnail((400, 400))
            img.save(output_path, "JPEG")
        except Exception as e:
            logger.warning(f"Thumbnail generation failed: {e}")

    def _save_to_history(self, result: ProcessingResult):
        """Save processing result to history."""
        try:
            history_file = self.config.get_history_file()
            history = []

            if os.path.exists(history_file):
                with open(history_file, 'r') as f:
                    history = json.load(f)

            entry = {
                'title': result.title,
                'volume': result.volume,
                'video_path': result.video_path,
                'thumbnail_path': result.thumbnail_path,
                'created_at': result.created_at,
                'video_duration': result.video_duration,
                'total_panels': result.total_panels,
                'selected_panels': result.selected_panels,
            }

            history.insert(0, entry)  # Add to beginning

            # Keep last 50 entries
            history = history[:50]

            with open(history_file, 'w') as f:
                json.dump(history, f, indent=2)

        except Exception as e:
            logger.warning(f"Failed to save history: {e}")

    def _cleanup_temp_dirs(self, dirs: List[str]):
        """Clean up temporary directories."""
        for dir_path in dirs:
            try:
                if os.path.exists(dir_path):
                    shutil.rmtree(dir_path)
                    self.log_message.emit(f"Cleaned up temp directory: {dir_path}")
            except Exception as e:
                logger.warning(f"Failed to cleanup {dir_path}: {e}")
