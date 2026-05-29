"""
Settings Page
API key management, preferences, and application settings.
"""

import os
import logging

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QCheckBox, QGroupBox, QFileDialog,
    QMessageBox, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from core.config_manager import ConfigManager
from gui.styles import AppTheme

logger = logging.getLogger(__name__)


class ApiKeyInput(QFrame):
    """Custom API key input with show/hide toggle."""

    def __init__(self, label: str, theme: AppTheme, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.setObjectName("card")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)

        self.label = QLabel(label)
        self.label.setMinimumWidth(100)
        layout.addWidget(self.label)

        self.input = QLineEdit()
        self.input.setEchoMode(QLineEdit.EchoMode.Password)
        self.input.setPlaceholderText("Enter API key...")
        layout.addWidget(self.input)

        self.show_btn = QPushButton("👁")
        self.show_btn.setMaximumWidth(40)
        self.show_btn.setCheckable(True)
        self.show_btn.clicked.connect(self._toggle_visibility)
        layout.addWidget(self.show_btn)

    def _toggle_visibility(self):
        if self.show_btn.isChecked():
            self.input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.input.setEchoMode(QLineEdit.EchoMode.Password)

    def get_key(self) -> str:
        return self.input.text().strip()

    def set_key(self, key: str):
        self.input.setText(key)

    def apply_theme(self, theme: AppTheme):
        self.theme = theme


class SettingsPage(QWidget):
    """Settings page with API keys and preferences."""

    theme_changed = pyqtSignal(bool)
    settings_saved = pyqtSignal()

    def __init__(self, config: ConfigManager, theme: AppTheme, parent=None):
        super().__init__(parent)
        self.config = config
        self.theme = theme
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Header
        header = QLabel("⚙ Settings")
        header.setObjectName("title")
        layout.addWidget(header)

        subtitle = QLabel("Configure API keys, preferences, and output options")
        subtitle.setObjectName("muted")
        layout.addWidget(subtitle)

        # API Keys Group
        api_group = QGroupBox("API Keys")
        api_layout = QVBoxLayout(api_group)
        api_layout.setSpacing(12)

        # Info label
        api_info = QLabel(
            "API keys are encrypted and stored locally on your machine. "
            "Free alternatives are available - see the AI and Voice sections below."
        )
        api_info.setWordWrap(True)
        api_info.setObjectName("muted")
        api_info.setStyleSheet(f"font-size: 12px; padding: 8px;")
        api_layout.addWidget(api_info)

        self.openai_key = ApiKeyInput("OpenAI:", self.theme)
        api_layout.addWidget(self.openai_key)

        self.gemini_key = ApiKeyInput("Gemini:", self.theme)
        api_layout.addWidget(self.gemini_key)

        self.elevenlabs_key = ApiKeyInput("ElevenLabs:", self.theme)
        api_layout.addWidget(self.elevenlabs_key)

        layout.addWidget(api_group)

        # AI Provider Settings
        ai_group = QGroupBox("AI Provider Settings")
        ai_layout = QVBoxLayout(ai_group)

        # Ollama settings
        ollama_info = QLabel(
            "Ollama is a free local AI option. Install from ollama.com, "
            "then download a vision model like 'llava' or 'bakllava'."
        )
        ollama_info.setWordWrap(True)
        ollama_info.setObjectName("muted")
        ai_layout.addWidget(ollama_info)

        ollama_url_layout = QHBoxLayout()
        ollama_url_layout.addWidget(QLabel("Ollama URL:"))
        self.ollama_url = QLineEdit()
        self.ollama_url.setPlaceholderText("http://localhost:11434")
        ollama_url_layout.addWidget(self.ollama_url)
        ai_layout.addLayout(ollama_url_layout)

        ollama_model_layout = QHBoxLayout()
        ollama_model_layout.addWidget(QLabel("Ollama Model:"))
        self.ollama_model = QComboBox()
        self.ollama_model.setEditable(True)
        self.ollama_model.addItems(["llava", "bakllava", "llava-phi3", "moondream"])
        ollama_model_layout.addWidget(self.ollama_model)
        ai_layout.addLayout(ollama_model_layout)

        layout.addWidget(ai_group)

        # Output Settings
        out_group = QGroupBox("Output Settings")
        out_layout = QVBoxLayout(out_group)

        dir_layout = QHBoxLayout()
        dir_layout.addWidget(QLabel("Output Folder:"))
        self.output_dir = QLineEdit()
        self.output_dir.setReadOnly(True)
        dir_layout.addWidget(self.output_dir)

        browse_btn = QPushButton("Browse...")
        browse_btn.setObjectName("secondary")
        browse_btn.setMaximumWidth(100)
        browse_btn.clicked.connect(self._browse_output_dir)
        dir_layout.addWidget(browse_btn)
        out_layout.addLayout(dir_layout)

        res_layout = QHBoxLayout()
        res_layout.addWidget(QLabel("Default Resolution:"))
        self.default_resolution = QComboBox()
        self.default_resolution.addItems(["720p HD", "1080p Full HD"])
        res_layout.addWidget(self.default_resolution)
        res_layout.addStretch()
        out_layout.addLayout(res_layout)

        layout.addWidget(out_group)

        # Appearance
        appear_group = QGroupBox("Appearance")
        appear_layout = QVBoxLayout(appear_group)

        self.dark_mode_check = QCheckBox("Dark Mode")
        self.dark_mode_check.setChecked(True)
        appear_layout.addWidget(self.dark_mode_check)

        layout.addWidget(appear_group)

        # Advanced
        adv_group = QGroupBox("Advanced")
        adv_layout = QVBoxLayout(adv_group)

        self.preserve_temp = QCheckBox("Preserve temporary files (for debugging)")
        adv_layout.addWidget(self.preserve_temp)

        self.auto_update = QCheckBox("Check for updates on startup")
        self.auto_update.setChecked(True)
        adv_layout.addWidget(self.auto_update)

        layout.addWidget(adv_group)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.save_btn = QPushButton("💾 Save Settings")
        self.save_btn.clicked.connect(self._save_settings)
        btn_layout.addWidget(self.save_btn)

        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.setObjectName("secondary")
        reset_btn.clicked.connect(self._reset_defaults)
        btn_layout.addWidget(reset_btn)

        layout.addLayout(btn_layout)
        layout.addStretch()

        scroll.setWidget(main_widget)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    def apply_theme(self, theme: AppTheme):
        """Apply theme."""
        self.theme = theme

    def _load_settings(self):
        """Load current settings into UI."""
        self.openai_key.set_key(self.config.get('openai_api_key', ''))
        self.gemini_key.set_key(self.config.get('gemini_api_key', ''))
        self.elevenlabs_key.set_key(self.config.get('elevenlabs_api_key', ''))

        self.ollama_url.setText(self.config.get('ollama_url', 'http://localhost:11434'))
        self.ollama_model.setCurrentText(self.config.get('ollama_model', 'llava'))

        self.output_dir.setText(self.config.get_output_dir())

        res = self.config.get('video_resolution', '720p')
        self.default_resolution.setCurrentIndex(0 if res == '720p' else 1)

        self.dark_mode_check.setChecked(self.config.get('dark_mode', True))
        self.preserve_temp.setChecked(self.config.get('preserve_temp_files', False))
        self.auto_update.setChecked(self.config.get('auto_update_check', True))

    def _save_settings(self):
        """Save settings from UI."""
        try:
            # API keys
            self.config.set('openai_api_key', self.openai_key.get_key())
            self.config.set('gemini_api_key', self.gemini_key.get_key())
            self.config.set('elevenlabs_api_key', self.elevenlabs_key.get_key())

            # Ollama
            self.config.set('ollama_url', self.ollama_url.text().strip() or 'http://localhost:11434')
            self.config.set('ollama_model', self.ollama_model.currentText())

            # Output
            res = "720p" if self.default_resolution.currentIndex() == 0 else "1080p"
            self.config.set('video_resolution', res)

            # Appearance
            dark_mode = self.dark_mode_check.isChecked()
            old_dark = self.config.get('dark_mode', True)
            self.config.set('dark_mode', dark_mode)

            # Advanced
            self.config.set('preserve_temp_files', self.preserve_temp.isChecked())
            self.config.set('auto_update_check', self.auto_update.isChecked())

            self.config.save()

            # Emit signals
            if dark_mode != old_dark:
                self.theme_changed.emit(dark_mode)

            self.settings_saved.emit()

            QMessageBox.information(self, "Saved", "Settings saved successfully!")

        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save settings:\n{e}")

    def _reset_defaults(self):
        """Reset all settings to defaults."""
        reply = QMessageBox.question(
            self, "Confirm Reset",
            "Reset all settings to defaults?\nThis will clear API keys.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.config.reset_to_defaults()
            self._load_settings()
            QMessageBox.information(self, "Reset", "Settings reset to defaults.")

    def _browse_output_dir(self):
        """Browse for output directory."""
        dir_path = QFileDialog.getExistingDirectory(
            self, "Select Output Directory",
            self.config.get_output_dir()
        )
        if dir_path:
            self.output_dir.setText(dir_path)
            self.config.set('output_directory', dir_path)
