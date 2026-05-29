"""
New Project Page
The main page for creating new manga recap projects.
Features drag-and-drop PDF upload, processing options, and real-time progress.
"""

import os
import logging
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QSpinBox, QProgressBar, QTextEdit,
    QCheckBox, QGroupBox, QFileDialog, QMessageBox, QFrame,
    QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QPixmap, QImage

from core.config_manager import ConfigManager
from core.worker import ProcessingWorker, ProcessingResult
from gui.styles import AppTheme

logger = logging.getLogger(__name__)


class DropZone(QFrame):
    """Drag-and-drop zone for PDF files."""

    file_dropped = pyqtSignal(str)

    def __init__(self, theme: AppTheme, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.setAcceptDrops(True)
        self.setMinimumHeight(200)
        self.setMaximumHeight(250)
        self._setup_ui()
        self._update_style()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.icon_label = QLabel("📄")
        self.icon_label.setStyleSheet("font-size: 48px;")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.icon_label)

        self.text_label = QLabel("Drag & Drop your Manga PDF here")
        self.text_label.setStyleSheet("font-size: 16px; font-weight: 600;")
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.text_label)

        self.sub_label = QLabel("or click to browse")
        self.sub_label.setStyleSheet("font-size: 13px;")
        self.sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.sub_label)

        self.browse_btn = QPushButton("Browse Files")
        self.browse_btn.setObjectName("secondary")
        self.browse_btn.setMaximumWidth(150)
        self.browse_btn.clicked.connect(self._browse_file)
        layout.addWidget(self.browse_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    def _update_style(self, dragging: bool = False):
        color = self.theme.accent if dragging else self.theme.border
        bg = self.theme.bg_card if not dragging else self.theme.bg_hover
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg};
                border: 3px dashed {color};
                border-radius: 16px;
            }}
        """)

    def apply_theme(self, theme: AppTheme):
        self.theme = theme
        self._update_style()

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if any(url.toLocalFile().lower().endswith('.pdf') for url in urls):
                event.acceptProposedAction()
                self._update_style(dragging=True)

    def dragLeaveEvent(self, event):
        self._update_style(dragging=False)

    def dropEvent(self, event: QDropEvent):
        self._update_style(dragging=False)
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.lower().endswith('.pdf'):
                self.file_dropped.emit(file_path)
                break

    def _browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Manga PDF", "",
            "PDF Files (*.pdf)"
        )
        if file_path:
            self.file_dropped.emit(file_path)


class LogConsole(QTextEdit):
    """Read-only log display with auto-scroll."""

    def __init__(self, theme: AppTheme, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setMaximumBlockCount(500)
        self.setPlaceholderText("Processing logs will appear here...")
        self.setStyleSheet(f"""
            QTextEdit {{
                background-color: {theme.bg_primary};
                border: 1px solid {theme.border};
                border-radius: 8px;
                padding: 8px;
                font-family: Consolas, Monaco, monospace;
                font-size: 11px;
                color: {theme.text_secondary};
            }}
        """)

    def append_log(self, message: str):
        self.append(message)
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())


class NewProjectPage(QWidget):
    """Page for creating new manga recap projects."""

    status_message = pyqtSignal(str)

    def __init__(self, config: ConfigManager, theme: AppTheme, parent=None):
        super().__init__(parent)
        self.config = config
        self.theme = theme
        self.worker = None
        self.current_pdf = ""
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)

        # Left column - Options
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(16)

        # Header
        header = QLabel("New Project")
        header.setObjectName("title")
        left_layout.addWidget(header)

        # Drop zone
        self.drop_zone = DropZone(self.theme)
        self.drop_zone.file_dropped.connect(self._on_pdf_dropped)
        left_layout.addWidget(self.drop_zone)

        # File info
        self.file_info = QLabel("No file selected")
        self.file_info.setObjectName("muted")
        left_layout.addWidget(self.file_info)

        # Manga Info Group
        info_group = QGroupBox("Manga Information")
        info_layout = QVBoxLayout(info_group)

        # Title input
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel("Title:"))
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Auto-detect or enter manga title")
        title_layout.addWidget(self.title_input)
        info_layout.addLayout(title_layout)

        # Volume input
        vol_layout = QHBoxLayout()
        vol_layout.addWidget(QLabel("Volume:"))
        self.volume_input = QLineEdit()
        self.volume_input.setPlaceholderText("Auto-detect or enter volume number")
        self.volume_input.setMaximumWidth(150)
        vol_layout.addWidget(self.volume_input)
        vol_layout.addStretch()
        info_layout.addLayout(vol_layout)

        left_layout.addWidget(info_group)

        # Processing Options Group
        proc_group = QGroupBox("Processing Options")
        proc_layout = QVBoxLayout(proc_group)

        # Vision provider
        vision_layout = QHBoxLayout()
        vision_layout.addWidget(QLabel("AI Vision:"))
        self.vision_provider = QComboBox()
        self.vision_provider.addItems(["OpenAI GPT-4o", "OpenAI GPT-4o-mini", "Google Gemini", "Ollama (Local)"])
        self.vision_provider.currentIndexChanged.connect(self._on_vision_changed)
        vision_layout.addWidget(self.vision_provider)
        proc_layout.addLayout(vision_layout)

        # Extraction level
        ext_layout = QHBoxLayout()
        ext_layout.addWidget(QLabel("Panel Detection:"))
        self.extraction_level = QComboBox()
        self.extraction_level.addItems(["Low (Faster)", "Medium (Balanced)", "High (Detailed)"])
        self.extraction_level.setCurrentIndex(1)
        ext_layout.addWidget(self.extraction_level)
        proc_layout.addLayout(ext_layout)

        # Summary style
        style_layout = QHBoxLayout()
        style_layout.addWidget(QLabel("Narration Style:"))
        self.summary_style = QComboBox()
        self.summary_style.addItems(["Dramatic (Epic)", "Casual (Friendly)", "Anime Style", "Concise (Brief)"])
        style_layout.addWidget(self.summary_style)
        proc_layout.addLayout(style_layout)

        # TTS Provider
        tts_layout = QHBoxLayout()
        tts_layout.addWidget(QLabel("Voice:"))
        self.tts_provider = QComboBox()
        self.tts_provider.addItems([
            "Microsoft Edge (Free)",
            "Kokoro TTS (Free/Local)",
            "ElevenLabs (Premium)",
            "System TTS (Free)"
        ])
        self.tts_provider.currentIndexChanged.connect(self._on_tts_changed)
        tts_layout.addWidget(self.tts_provider)
        proc_layout.addLayout(tts_layout)

        # Voice selection (populated based on provider)
        voice_layout = QHBoxLayout()
        voice_layout.addWidget(QLabel("Voice ID:"))
        self.voice_select = QComboBox()
        self.voice_select.setEnabled(False)
        self.voice_select.addItem("Default")
        voice_layout.addWidget(self.voice_select)
        proc_layout.addLayout(voice_layout)

        # Max panels
        max_layout = QHBoxLayout()
        max_layout.addWidget(QLabel("Max Panels:"))
        self.max_panels = QSpinBox()
        self.max_panels.setRange(5, 50)
        self.max_panels.setValue(20)
        max_layout.addWidget(self.max_panels)
        max_layout.addStretch()
        proc_layout.addLayout(max_layout)

        # Video options
        vid_layout = QHBoxLayout()
        vid_layout.addWidget(QLabel("Resolution:"))
        self.video_resolution = QComboBox()
        self.video_resolution.addItems(["720p HD", "1080p Full HD"])
        vid_layout.addWidget(self.video_resolution)
        proc_layout.addLayout(vid_layout)

        # Checkboxes
        self.ken_burns_check = QCheckBox("Ken Burns zoom effect")
        self.ken_burns_check.setChecked(True)
        proc_layout.addWidget(self.ken_burns_check)

        self.text_overlay_check = QCheckBox("Show scene titles")
        self.text_overlay_check.setChecked(True)
        proc_layout.addWidget(self.text_overlay_check)

        self.chapter_titles_check = QCheckBox("Include chapter titles")
        self.chapter_titles_check.setChecked(True)
        proc_layout.addWidget(self.chapter_titles_check)

        left_layout.addWidget(proc_group)

        # Action buttons
        btn_layout = QHBoxLayout()

        self.start_btn = QPushButton("Start Processing")
        self.start_btn.setEnabled(False)
        self.start_btn.clicked.connect(self._start_processing)
        btn_layout.addWidget(self.start_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("danger")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self._cancel_processing)
        btn_layout.addWidget(self.cancel_btn)

        left_layout.addLayout(btn_layout)
        left_layout.addStretch()

        left_scroll.setWidget(left_widget)
        layout.addWidget(left_scroll, 2)

        # Right column - Preview & Progress
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setSpacing(16)

        # Preview area
        preview_header = QLabel("Preview")
        preview_header.setObjectName("subtitle")
        preview_header.setStyleSheet("font-size: 16px; font-weight: 600;")
        right_layout.addWidget(preview_header)

        self.preview_frame = QFrame()
        self.preview_frame.setObjectName("card")
        self.preview_frame.setMinimumHeight(300)
        preview_layout = QVBoxLayout(self.preview_frame)

        self.preview_label = QLabel("PDF pages will be previewed here")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setObjectName("muted")
        preview_layout.addWidget(self.preview_label)

        right_layout.addWidget(self.preview_frame)

        # Progress section
        progress_header = QLabel("Progress")
        progress_header.setObjectName("subtitle")
        progress_header.setStyleSheet("font-size: 16px; font-weight: 600;")
        right_layout.addWidget(progress_header)

        # Current step
        self.step_label = QLabel("Waiting to start...")
        self.step_label.setStyleSheet(f"font-weight: 600; color: {self.theme.accent};")
        right_layout.addWidget(self.step_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setMinimumHeight(24)
        right_layout.addWidget(self.progress_bar)

        # Log console
        self.log_console = LogConsole(self.theme)
        self.log_console.setMinimumHeight(200)
        right_layout.addWidget(self.log_console)

        layout.addWidget(right_widget, 3)

    def apply_theme(self, theme: AppTheme):
        """Apply theme to page."""
        self.theme = theme
        self.drop_zone.apply_theme(theme)
        self.log_console.setStyleSheet(f"""
            QTextEdit {{
                background-color: {theme.bg_primary};
                border: 1px solid {theme.border};
                border-radius: 8px;
                padding: 8px;
                font-family: Consolas, Monaco, monospace;
                font-size: 11px;
                color: {theme.text_secondary};
            }}
        """)
        self.step_label.setStyleSheet(f"font-weight: 600; color: {theme.accent};")

    def _on_pdf_dropped(self, file_path: str):
        """Handle PDF file drop."""
        self.current_pdf = file_path
        file_name = Path(file_path).name

        # Update UI
        self.drop_zone.text_label.setText(file_name)
        self.drop_zone.sub_label.setText(f"{os.path.getsize(file_path) / 1024 / 1024:.1f} MB")
        self.file_info.setText(f"Selected: {file_path}")

        # Try to detect metadata
        self._detect_metadata(file_path)

        self.start_btn.setEnabled(True)

    def _detect_metadata(self, file_path: str):
        """Auto-detect manga metadata from PDF."""
        try:
            from core.manga_extraction import MangaExtractor
            extractor = MangaExtractor()
            metadata = extractor.detect_manga_metadata(file_path)

            if metadata.get('title'):
                self.title_input.setText(metadata['title'])
            if metadata.get('volume'):
                self.volume_input.setText(str(metadata['volume']))

            self.log_console.append_log(f"Detected: {metadata.get('title', 'Unknown')} Vol.{metadata.get('volume', '?')} ({metadata.get('total_pages', 0)} pages)")

        except Exception as e:
            self.log_console.append_log(f"Metadata detection failed: {e}")

    def _on_vision_changed(self, index: int):
        """Handle vision provider change."""
        providers = ["openai", "openai", "gemini", "ollama"]
        provider = providers[index]

        # Update voice options based on provider
        if provider == "openai" and index == 0:
            self.vision_provider.setToolTip("GPT-4o - Best quality, higher cost")
        elif provider == "openai" and index == 1:
            self.vision_provider.setToolTip("GPT-4o-mini - Good quality, lower cost")

    def _on_tts_changed(self, index: int):
        """Handle TTS provider change."""
        self.voice_select.clear()

        if index == 0:  # Edge
            self.voice_select.addItems([
                "en-US-AriaNeural (Female)",
                "en-US-GuyNeural (Male)",
                "en-US-JennyNeural (Female)",
                "en-GB-SoniaNeural (UK Female)",
                "ja-JP-NanamiNeural (Japanese)"
            ])
            self.voice_select.setEnabled(True)
        elif index == 1:  # Kokoro
            self.voice_select.addItems([
                "af_bella (American Female)",
                "af_sarah (American Female)",
                "am_adam (American Male)",
                "am_michael (American Male)",
                "bf_emma (British Female)",
                "bm_george (British Male)"
            ])
            self.voice_select.setEnabled(True)
        elif index == 2:  # ElevenLabs
            self.voice_select.addItem("Loading voices...")
            self.voice_select.setEnabled(False)
            self._load_elevenlabs_voices()
        else:  # System
            self.voice_select.addItem("Default System Voice")
            self.voice_select.setEnabled(False)

    def _load_elevenlabs_voices(self):
        """Load ElevenLabs voices in background."""
        api_key = self.config.get_api_key('elevenlabs')
        if api_key:
            try:
                from core.narration import ElevenLabsProvider
                provider = ElevenLabsProvider(api_key)
                voices = provider.get_voices()
                self.voice_select.clear()
                for voice in voices:
                    self.voice_select.addItem(f"{voice['name']} ({voice['category']})", voice['id'])
                self.voice_select.setEnabled(True)
            except Exception as e:
                self.voice_select.clear()
                self.voice_select.addItem(f"Error loading voices: {e}")
                self.voice_select.setEnabled(False)
        else:
            self.voice_select.clear()
            self.voice_select.addItem("Add API key in Settings")
            self.voice_select.setEnabled(False)

    def _get_processing_options(self) -> dict:
        """Get processing options from UI."""
        vision_map = {0: ("openai", "gpt-4o"), 1: ("openai", "gpt-4o-mini"), 2: ("gemini", "gemini-pro-vision"), 3: ("ollama", "llava")}
        tts_map = {0: ("edge", None), 1: ("kokoro", None), 2: ("elevenlabs", None), 3: ("pyttsx3", None)}
        ext_map = {0: "low", 1: "medium", 2: "high"}
        style_map = {0: "dramatic", 1: "casual", 2: "anime", 3: "concise"}
        res_map = {0: "720p", 1: "1080p"}

        vision_provider, vision_model = vision_map[self.vision_provider.currentIndex()]
        tts_provider, _ = tts_map[self.tts_provider.currentIndex()]

        voice_id = None
        if self.voice_select.isEnabled():
            voice_id = self.voice_select.currentData() or self.voice_select.currentText()

        return {
            'title': self.title_input.text() or "Manga Recap",
            'volume': self.volume_input.text() or "1",
            'vision_provider': vision_provider,
            'vision_model': vision_model,
            'extraction_level': ext_map[self.extraction_level.currentIndex()],
            'summary_style': style_map[self.summary_style.currentIndex()],
            'tts_provider': tts_provider,
            'tts_voice': voice_id,
            'max_panels': self.max_panels.value(),
            'video_resolution': res_map[self.video_resolution.currentIndex()],
            'ken_burns': self.ken_burns_check.isChecked(),
            'text_overlay': self.text_overlay_check.isChecked(),
            'include_chapter_titles': self.chapter_titles_check.isChecked(),
            'output_dir': self.config.get_output_dir(),
            'transition_type': 'fade'
        }

    def _start_processing(self):
        """Start the processing workflow."""
        if not self.current_pdf or not os.path.exists(self.current_pdf):
            QMessageBox.warning(self, "No File", "Please select a PDF file first.")
            return

        # Check API keys
        options = self._get_processing_options()

        if options['vision_provider'] == 'openai' and not self.config.get_api_key('openai'):
            QMessageBox.warning(self, "API Key Missing",
                               "OpenAI API key is required. Please add it in Settings.")
            return

        if options['vision_provider'] == 'gemini' and not self.config.get_api_key('gemini'):
            QMessageBox.warning(self, "API Key Missing",
                               "Gemini API key is required. Please add it in Settings.")
            return

        if options['tts_provider'] == 'elevenlabs' and not self.config.get_api_key('elevenlabs'):
            QMessageBox.warning(self, "API Key Missing",
                               "ElevenLabs API key is required. Please add it in Settings.")
            return

        # Reset UI
        self.progress_bar.setValue(0)
        self.log_console.clear()
        self.step_label.setText("Initializing...")

        # Disable controls
        self.start_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)

        # Create and start worker
        self.worker = ProcessingWorker(
            pdf_path=self.current_pdf,
            config_manager=self.config,
            options=options
        )

        self.worker.progress_updated.connect(self._on_progress)
        self.worker.step_changed.connect(self._on_step)
        self.worker.log_message.connect(self._on_log)
        self.worker.processing_complete.connect(self._on_complete)
        self.worker.processing_cancelled.connect(self._on_cancelled)

        self.worker.start()

        self.status_message.emit("Processing started...")

    def _cancel_processing(self):
        """Cancel the current processing job."""
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.cancel_btn.setEnabled(False)
            self.step_label.setText("Cancelling...")

    def _on_progress(self, message: str, percent: int):
        """Handle progress update."""
        self.progress_bar.setValue(percent)
        self.status_message.emit(message)

    def _on_step(self, step: str):
        """Handle step change."""
        self.step_label.setText(step)

    def _on_log(self, message: str):
        """Handle log message."""
        self.log_console.append_log(message)

    def _on_complete(self, result: ProcessingResult):
        """Handle processing completion."""
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)

        if result.success:
            self.progress_bar.setValue(100)
            self.step_label.setText("Complete!")

            msg = QMessageBox(self)
            msg.setWindowTitle("Success!")
            msg.setText("Your manga recap video has been created!")
            msg.setInformativeText(
                f"Title: {result.title}\n"
                f"Volume: {result.volume}\n"
                f"Video: {result.video_path}\n"
                f"Duration: {result.video_duration:.1f}s\n"
                f"Panels: {result.selected_panels}/{result.total_panels}"
            )
            msg.setIcon(QMessageBox.Icon.Information)

            open_btn = msg.addButton("Open Video", QMessageBox.ButtonRole.ActionRole)
            msg.addButton("OK", QMessageBox.ButtonRole.AcceptRole)

            msg.exec()

            if msg.clickedButton() == open_btn:
                os.startfile(result.video_path)

            self.status_message.emit("Processing complete!")
        else:
            self.progress_bar.setValue(0)
            self.step_label.setText(f"Error: {result.error_message}")

            QMessageBox.critical(self, "Processing Failed",
                                f"An error occurred:\n\n{result.error_message}")

            self.status_message.emit("Processing failed")

    def _on_cancelled(self):
        """Handle processing cancellation."""
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.step_label.setText("Cancelled")
        self.status_message.emit("Processing cancelled")
