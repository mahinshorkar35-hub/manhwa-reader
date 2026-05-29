"""
Main Window Module
The primary application window with sidebar navigation and stacked pages.
"""

import os
import sys
import logging
from pathlib import Path

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QFrame,
    QSizePolicy, QApplication, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QIcon, QFont, QFontDatabase, QPainter, QColor

from core.config_manager import ConfigManager
from gui.styles import AppTheme
from gui.new_project_page import NewProjectPage
from gui.library_page import LibraryPage
from gui.settings_page import SettingsPage

logger = logging.getLogger(__name__)


class SidebarButton(QPushButton):
    """Custom sidebar navigation button."""

    def __init__(self, icon_text: str, label: str, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(48)
        self.setMaximumHeight(48)

        self.icon_text = icon_text
        self.label_text = label

        self.update_style()

    def update_style(self):
        """Update button appearance based on state."""
        theme = getattr(self, '_theme', None)
        if not theme:
            return

        if self.isChecked():
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {theme.accent};
                    color: white;
                    border: none;
                    border-radius: 10px;
                    text-align: left;
                    padding-left: 16px;
                    font-size: 14px;
                    font-weight: 600;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {theme.text_secondary};
                    border: none;
                    border-radius: 10px;
                    text-align: left;
                    padding-left: 16px;
                    font-size: 14px;
                    font-weight: 500;
                }}
                QPushButton:hover {{
                    background-color: {theme.bg_hover};
                    color: {theme.text_primary};
                }}
            """)


class Sidebar(QFrame):
    """Application sidebar with navigation."""

    navigation_changed = pyqtSignal(int)

    def __init__(self, config: ConfigManager, parent=None):
        super().__init__(parent)
        self.config = config
        self.buttons = []
        self._setup_ui()

    def _setup_ui(self):
        self.setObjectName("sidebar")
        self.setMaximumWidth(260)
        self.setMinimumWidth(220)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 20, 16, 20)
        layout.setSpacing(8)

        # App logo/title
        logo_layout = QHBoxLayout()
        logo_icon = QLabel("📖")
        logo_icon.setStyleSheet("font-size: 28px;")
        logo_layout.addWidget(logo_icon)

        logo_text = QLabel("MangaRecap")
        logo_text.setStyleSheet("""
            font-size: 20px;
            font-weight: 700;
        """)
        logo_layout.addWidget(logo_text)
        logo_layout.addStretch()
        layout.addLayout(logo_layout)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: transparent; margin: 8px 0;")
        layout.addWidget(separator)

        # Navigation buttons
        nav_items = [
            ("+", "New Project", 0),
            ("🎬", "Library", 1),
            ("⚙", "Settings", 2),
        ]

        for icon, label, page_id in nav_items:
            btn = SidebarButton(icon, label)
            btn.setText(f"  {icon}  {label}")
            btn.clicked.connect(lambda checked, pid=page_id: self._on_button_clicked(pid))
            self.buttons.append(btn)
            layout.addWidget(btn)

        layout.addStretch()

        # Version label
        version = QLabel("v1.0.0")
        version.setObjectName("muted")
        version.setStyleSheet("font-size: 11px;")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version)

    def _on_button_clicked(self, page_id: int):
        """Handle navigation button click."""
        for i, btn in enumerate(self.buttons):
            btn.setChecked(i == page_id)
            btn.update_style()
        self.navigation_changed.emit(page_id)

    def set_active_page(self, page_id: int):
        """Set active page without emitting signal."""
        for i, btn in enumerate(self.buttons):
            btn.setChecked(i == page_id)
            btn.update_style()

    def apply_theme(self, theme: AppTheme):
        """Apply theme to sidebar."""
        for btn in self.buttons:
            btn._theme = theme
            btn.update_style()


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.config = ConfigManager()
        self.dark_mode = self.config.get('dark_mode', True)
        self.theme = AppTheme(dark_mode=self.dark_mode)

        self.setWindowTitle("MangaRecap - Manga to Video Recap")
        self.setMinimumSize(1200, 800)

        # Restore window size
        w = self.config.get('window_width', 1400)
        h = self.config.get('window_height', 900)
        self.resize(w, h)

        self._setup_ui()
        self._apply_theme()

    def _setup_ui(self):
        """Set up the main window UI."""
        central = QWidget()
        self.setCentralWidget(central)

        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Sidebar
        self.sidebar = Sidebar(self.config)
        self.sidebar.navigation_changed.connect(self._on_navigate)
        layout.addWidget(self.sidebar)

        # Content area with stacked pages
        self.stack = QStackedWidget()

        # Pages
        self.new_project_page = NewProjectPage(self.config, self.theme)
        self.new_project_page.status_message.connect(self._show_status)

        self.library_page = LibraryPage(self.config, self.theme)
        self.library_page.open_video.connect(self._open_video)

        self.settings_page = SettingsPage(self.config, self.theme)
        self.settings_page.theme_changed.connect(self._on_theme_changed)
        self.settings_page.settings_saved.connect(self._on_settings_saved)

        self.stack.addWidget(self.new_project_page)
        self.stack.addWidget(self.library_page)
        self.stack.addWidget(self.settings_page)

        layout.addWidget(self.stack, 1)

        # Set initial page
        self.sidebar.set_active_page(0)

        # Status bar
        self.statusBar().showMessage("Ready")
        self.statusBar().setStyleSheet(f"color: {self.theme.text_muted};")

    def _apply_theme(self):
        """Apply current theme to the application."""
        self.setPalette(self.theme.get_palette())
        self.setStyleSheet(self.theme.get_stylesheet())
        self.sidebar.apply_theme(self.theme)

        # Update pages
        self.new_project_page.apply_theme(self.theme)
        self.library_page.apply_theme(self.theme)
        self.settings_page.apply_theme(self.theme)

    def _on_navigate(self, page_id: int):
        """Handle navigation to a page."""
        self.stack.setCurrentIndex(page_id)

        if page_id == 1:
            self.library_page.refresh()

    def _on_theme_changed(self, dark_mode: bool):
        """Handle theme change."""
        self.dark_mode = dark_mode
        self.theme = AppTheme(dark_mode=dark_mode)
        self._apply_theme()

    def _on_settings_saved(self):
        """Handle settings save."""
        self.statusBar().showMessage("Settings saved successfully", 3000)

    def _show_status(self, message: str):
        """Show status message."""
        self.statusBar().showMessage(message, 5000)

    def _open_video(self, video_path: str):
        """Open a video file."""
        if os.path.exists(video_path):
            os.startfile(video_path)
        else:
            QMessageBox.warning(self, "File Not Found",
                               f"Video file not found:\n{video_path}")

    def closeEvent(self, event):
        """Handle window close - save settings."""
        # Save window size
        self.config.set('window_width', self.width())
        self.config.set('window_height', self.height())
        self.config.save()

        # Check if processing is running
        if hasattr(self.new_project_page, 'worker') and self.new_project_page.worker and self.new_project_page.worker.isRunning():
            reply = QMessageBox.question(
                self, "Confirm Exit",
                "A processing job is still running. Are you sure you want to exit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.new_project_page.worker.cancel()
                self.new_project_page.worker.wait(3000)
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
