"""
Library Page
Displays history of generated recap videos with thumbnails and playback.
"""

import os
import json
import logging
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QSizePolicy, QMessageBox, QFileDialog,
    QGridLayout, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QIcon, QCursor

from core.config_manager import ConfigManager
from gui.styles import AppTheme

logger = logging.getLogger(__name__)


class VideoCard(QFrame):
    """Card displaying a recap video with thumbnail and info."""

    play_clicked = pyqtSignal(str)
    delete_clicked = pyqtSignal(str)

    def __init__(self, entry: dict, theme: AppTheme, parent=None):
        super().__init__(parent)
        self.entry = entry
        self.theme = theme
        self.video_path = entry.get('video_path', '')
        self._setup_ui()

    def _setup_ui(self):
        self.setObjectName("card")
        self.setMaximumWidth(300)
        self.setMinimumWidth(260)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Thumbnail
        thumb_path = self.entry.get('thumbnail_path', '')
        self.thumb = QLabel()
        self.thumb.setMinimumHeight(160)
        self.thumb.setMaximumHeight(180)
        self.thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumb.setStyleSheet(f"""
            background-color: {self.theme.bg_primary};
            border-radius: 8px;
        """)

        if thumb_path and os.path.exists(thumb_path):
            pixmap = QPixmap(thumb_path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(280, 170, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                       Qt.TransformationMode.SmoothTransformation)
                self.thumb.setPixmap(scaled)
        else:
            self.thumb.setText("🎬")
            self.thumb.setStyleSheet(f"""
                background-color: {self.theme.bg_primary};
                border-radius: 8px;
                font-size: 48px;
            """)

        layout.addWidget(self.thumb)

        # Title
        title = self.entry.get('title', 'Unknown')
        volume = self.entry.get('volume', '')
        display_title = f"{title}"
        if volume:
            display_title += f" Vol.{volume}"

        self.title_label = QLabel(display_title)
        self.title_label.setStyleSheet(f"""
            font-weight: 700;
            font-size: 14px;
            color: {self.theme.text_primary};
        """)
        self.title_label.setWordWrap(True)
        layout.addWidget(self.title_label)

        # Info
        info_text = f"{self.entry.get('selected_panels', 0)} panels"
        duration = self.entry.get('video_duration', 0)
        if duration:
            info_text += f" | {duration:.0f}s"

        self.info_label = QLabel(info_text)
        self.info_label.setStyleSheet(f"font-size: 12px; color: {self.theme.text_muted};")
        layout.addWidget(self.info_label)

        # Date
        created = self.entry.get('created_at', '')
        if created:
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(created)
                date_str = dt.strftime("%Y-%m-%d %H:%M")
            except:
                date_str = created[:16]

            self.date_label = QLabel(date_str)
            self.date_label.setStyleSheet(f"font-size: 11px; color: {self.theme.text_muted};")
            layout.addWidget(self.date_label)

        # Buttons
        btn_layout = QHBoxLayout()

        play_btn = QPushButton("▶ Play")
        play_btn.setMaximumHeight(32)
        play_btn.clicked.connect(lambda: self.play_clicked.emit(self.video_path))
        btn_layout.addWidget(play_btn)

        delete_btn = QPushButton("🗑")
        delete_btn.setObjectName("danger")
        delete_btn.setMaximumWidth(40)
        delete_btn.setMaximumHeight(32)
        delete_btn.clicked.connect(lambda: self.delete_clicked.emit(self.video_path))
        btn_layout.addWidget(delete_btn)

        layout.addLayout(btn_layout)

    def mouseDoubleClickEvent(self, event):
        """Double-click to play."""
        self.play_clicked.emit(self.video_path)


class LibraryPage(QWidget):
    """Page displaying library of generated recaps."""

    open_video = pyqtSignal(str)

    def __init__(self, config: ConfigManager, theme: AppTheme, parent=None):
        super().__init__(parent)
        self.config = config
        self.theme = theme
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()

        header = QLabel("Library")
        header.setObjectName("title")
        header_layout.addWidget(header)

        header_layout.addStretch()

        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setObjectName("secondary")
        refresh_btn.setMaximumWidth(120)
        refresh_btn.clicked.connect(self.refresh)
        header_layout.addWidget(refresh_btn)

        open_folder_btn = QPushButton("📂 Output Folder")
        open_folder_btn.setObjectName("secondary")
        open_folder_btn.setMaximumWidth(150)
        open_folder_btn.clicked.connect(self._open_output_folder)
        header_layout.addWidget(open_folder_btn)

        layout.addLayout(header_layout)

        # Subtitle
        subtitle = QLabel("Your generated manga recap videos")
        subtitle.setObjectName("muted")
        layout.addWidget(subtitle)

        # Scroll area for cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.cards_widget = QWidget()
        self.cards_layout = QGridLayout(self.cards_widget)
        self.cards_layout.setSpacing(16)

        scroll.setWidget(self.cards_widget)
        layout.addWidget(scroll)

    def apply_theme(self, theme: AppTheme):
        """Apply theme."""
        self.theme = theme
        self.refresh()

    def refresh(self):
        """Refresh the library display."""
        # Clear existing cards
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Load history
        history = self._load_history()

        if not history:
            empty_label = QLabel("No recaps yet. Create your first manga recap!")
            empty_label.setObjectName("muted")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.cards_layout.addWidget(empty_label, 0, 0)
            return

        # Create cards
        for i, entry in enumerate(history):
            row = i // 3
            col = i % 3
            card = VideoCard(entry, self.theme)
            card.play_clicked.connect(self.open_video.emit)
            card.delete_clicked.connect(self._delete_entry)
            self.cards_layout.addWidget(card, row, col)

    def _load_history(self) -> list:
        """Load history from file."""
        history_file = self.config.get_history_file()
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load history: {e}")
        return []

    def _delete_entry(self, video_path: str):
        """Delete a history entry."""
        reply = QMessageBox.question(
            self, "Confirm Delete",
            "Delete this recap from history?\n(This won't delete the video file.)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            history = self._load_history()
            history = [h for h in history if h.get('video_path') != video_path]

            try:
                with open(self.config.get_history_file(), 'w') as f:
                    json.dump(history, f, indent=2)
                self.refresh()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to delete: {e}")

    def _open_output_folder(self):
        """Open the output folder in file explorer."""
        output_dir = self.config.get_output_dir()
        if os.path.exists(output_dir):
            os.startfile(output_dir)
        else:
            QMessageBox.warning(self, "Not Found", f"Output folder not found:\n{output_dir}")
