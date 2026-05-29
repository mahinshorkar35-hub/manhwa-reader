"""
Styles Module
Defines the modern dark/light theme stylesheets for the application.
"""

from PyQt6.QtGui import QColor, QPalette, QFont
from PyQt6.QtCore import Qt


class AppTheme:
    """Application theme colors and fonts."""

    # Dark theme colors
    DARK_BG_PRIMARY = "#1a1a2e"
    DARK_BG_SECONDARY = "#16213e"
    DARK_BG_TERTIARY = "#0f3460"
    DARK_BG_CARD = "#1e1e3f"
    DARK_BG_INPUT = "#252545"
    DARK_BG_HOVER = "#2a2a55"

    DARK_TEXT_PRIMARY = "#eaeaea"
    DARK_TEXT_SECONDARY = "#a0a0b8"
    DARK_TEXT_MUTED = "#6e6e8a"

    DARK_ACCENT = "#e94560"
    DARK_ACCENT_HOVER = "#ff6b81"
    DARK_ACCENT_SECONDARY = "#533483"

    DARK_BORDER = "#2d2d4a"
    DARK_SUCCESS = "#4ecca3"
    DARK_WARNING = "#f4d03f"
    DARK_ERROR = "#e74c3c"

    # Light theme colors
    LIGHT_BG_PRIMARY = "#f8f9fa"
    LIGHT_BG_SECONDARY = "#ffffff"
    LIGHT_BG_TERTIARY = "#e9ecef"
    LIGHT_BG_CARD = "#ffffff"
    LIGHT_BG_INPUT = "#f1f3f4"
    LIGHT_BG_HOVER = "#e8eaed"

    LIGHT_TEXT_PRIMARY = "#202124"
    LIGHT_TEXT_SECONDARY = "#5f6368"
    LIGHT_TEXT_MUTED = "#80868b"

    LIGHT_ACCENT = "#e94560"
    LIGHT_ACCENT_HOVER = "#c73e54"
    LIGHT_ACCENT_SECONDARY = "#533483"

    LIGHT_BORDER = "#dadce0"
    LIGHT_SUCCESS = "#34a853"
    LIGHT_WARNING = "#f9ab00"
    LIGHT_ERROR = "#ea4335"

    def __init__(self, dark_mode: bool = True):
        self.dark_mode = dark_mode
        self._setup_colors()
        self._setup_fonts()

    def _setup_colors(self):
        """Set up colors based on theme."""
        if self.dark_mode:
            self.bg_primary = self.DARK_BG_PRIMARY
            self.bg_secondary = self.DARK_BG_SECONDARY
            self.bg_tertiary = self.DARK_BG_TERTIARY
            self.bg_card = self.DARK_BG_CARD
            self.bg_input = self.DARK_BG_INPUT
            self.bg_hover = self.DARK_BG_HOVER

            self.text_primary = self.DARK_TEXT_PRIMARY
            self.text_secondary = self.DARK_TEXT_SECONDARY
            self.text_muted = self.DARK_TEXT_MUTED

            self.accent = self.DARK_ACCENT
            self.accent_hover = self.DARK_ACCENT_HOVER
            self.accent_secondary = self.DARK_ACCENT_SECONDARY

            self.border = self.DARK_BORDER
            self.success = self.DARK_SUCCESS
            self.warning = self.DARK_WARNING
            self.error = self.DARK_ERROR
        else:
            self.bg_primary = self.LIGHT_BG_PRIMARY
            self.bg_secondary = self.LIGHT_BG_SECONDARY
            self.bg_tertiary = self.LIGHT_BG_TERTIARY
            self.bg_card = self.LIGHT_BG_CARD
            self.bg_input = self.LIGHT_BG_INPUT
            self.bg_hover = self.LIGHT_BG_HOVER

            self.text_primary = self.LIGHT_TEXT_PRIMARY
            self.text_secondary = self.LIGHT_TEXT_SECONDARY
            self.text_muted = self.LIGHT_TEXT_MUTED

            self.accent = self.LIGHT_ACCENT
            self.accent_hover = self.LIGHT_ACCENT_HOVER
            self.accent_secondary = self.LIGHT_ACCENT_SECONDARY

            self.border = self.LIGHT_BORDER
            self.success = self.LIGHT_SUCCESS
            self.warning = self.LIGHT_WARNING
            self.error = self.LIGHT_ERROR

    def _setup_fonts(self):
        """Set up fonts."""
        self.font_family = "Segoe UI, Roboto, Helvetica, Arial, sans-serif"
        self.font_mono = "Consolas, Monaco, 'Courier New', monospace"

    def get_palette(self) -> QPalette:
        """Get QPalette for the theme."""
        palette = QPalette()

        if self.dark_mode:
            palette.setColor(QPalette.ColorRole.Window, QColor(self.bg_primary))
            palette.setColor(QPalette.ColorRole.WindowText, QColor(self.text_primary))
            palette.setColor(QPalette.ColorRole.Base, QColor(self.bg_input))
            palette.setColor(QPalette.ColorRole.AlternateBase, QColor(self.bg_secondary))
            palette.setColor(QPalette.ColorRole.Text, QColor(self.text_primary))
            palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(self.text_muted))
            palette.setColor(QPalette.ColorRole.Button, QColor(self.bg_tertiary))
            palette.setColor(QPalette.ColorRole.ButtonText, QColor(self.text_primary))
            palette.setColor(QPalette.ColorRole.Highlight, QColor(self.accent))
            palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
            palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(self.bg_card))
            palette.setColor(QPalette.ColorRole.ToolTipText, QColor(self.text_primary))
        else:
            palette.setColor(QPalette.ColorRole.Window, QColor(self.bg_primary))
            palette.setColor(QPalette.ColorRole.WindowText, QColor(self.text_primary))
            palette.setColor(QPalette.ColorRole.Base, QColor(self.bg_input))
            palette.setColor(QPalette.ColorRole.AlternateBase, QColor(self.bg_secondary))
            palette.setColor(QPalette.ColorRole.Text, QColor(self.text_primary))
            palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(self.text_muted))
            palette.setColor(QPalette.ColorRole.Button, QColor(self.bg_tertiary))
            palette.setColor(QPalette.ColorRole.ButtonText, QColor(self.text_primary))
            palette.setColor(QPalette.ColorRole.Highlight, QColor(self.accent))
            palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
            palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(self.bg_card))
            palette.setColor(QPalette.ColorRole.ToolTipText, QColor(self.text_primary))

        return palette

    def get_stylesheet(self) -> str:
        """Get the main application stylesheet."""
        return f"""
        QMainWindow {{
            background-color: {self.bg_primary};
            color: {self.text_primary};
        }}

        QWidget {{
            font-family: {self.font_family};
            font-size: 13px;
        }}

        QPushButton {{
            background-color: {self.accent};
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 20px;
            font-weight: 600;
            font-size: 13px;
        }}

        QPushButton:hover {{
            background-color: {self.accent_hover};
        }}

        QPushButton:pressed {{
            background-color: {self.accent};
        }}

        QPushButton:disabled {{
            background-color: {self.text_muted};
            color: {self.bg_primary};
        }}

        QPushButton#secondary {{
            background-color: {self.bg_tertiary};
            color: {self.text_primary};
            border: 1px solid {self.border};
        }}

        QPushButton#secondary:hover {{
            background-color: {self.bg_hover};
        }}

        QPushButton#danger {{
            background-color: {self.error};
        }}

        QPushButton#danger:hover {{
            background-color: #c0392b;
        }}

        QLineEdit {{
            background-color: {self.bg_input};
            color: {self.text_primary};
            border: 2px solid {self.border};
            border-radius: 8px;
            padding: 10px 14px;
            font-size: 13px;
        }}

        QLineEdit:focus {{
            border-color: {self.accent};
        }}

        QLineEdit::placeholder {{
            color: {self.text_muted};
        }}

        QTextEdit {{
            background-color: {self.bg_input};
            color: {self.text_primary};
            border: 2px solid {self.border};
            border-radius: 8px;
            padding: 10px;
            font-family: {self.font_mono};
            font-size: 12px;
        }}

        QTextEdit:focus {{
            border-color: {self.accent};
        }}

        QComboBox {{
            background-color: {self.bg_input};
            color: {self.text_primary};
            border: 2px solid {self.border};
            border-radius: 8px;
            padding: 10px 14px;
            min-width: 150px;
        }}

        QComboBox:hover {{
            border-color: {self.accent};
        }}

        QComboBox::drop-down {{
            border: none;
            width: 30px;
        }}

        QComboBox::down-arrow {{
            image: none;
            border: none;
        }}

        QComboBox QAbstractItemView {{
            background-color: {self.bg_card};
            color: {self.text_primary};
            border: 1px solid {self.border};
            selection-background-color: {self.accent};
            selection-color: white;
            border-radius: 8px;
        }}

        QSpinBox, QDoubleSpinBox {{
            background-color: {self.bg_input};
            color: {self.text_primary};
            border: 2px solid {self.border};
            border-radius: 8px;
            padding: 8px;
        }}

        QSpinBox:focus, QDoubleSpinBox:focus {{
            border-color: {self.accent};
        }}

        QSlider::groove:horizontal {{
            height: 6px;
            background: {self.border};
            border-radius: 3px;
        }}

        QSlider::handle:horizontal {{
            background: {self.accent};
            width: 18px;
            height: 18px;
            margin: -6px 0;
            border-radius: 9px;
        }}

        QSlider::sub-page:horizontal {{
            background: {self.accent};
            border-radius: 3px;
        }}

        QProgressBar {{
            border: none;
            border-radius: 6px;
            background-color: {self.border};
            text-align: center;
            color: white;
            font-weight: 600;
        }}

        QProgressBar::chunk {{
            background-color: {self.accent};
            border-radius: 6px;
        }}

        QScrollBar:vertical {{
            background-color: {self.bg_secondary};
            width: 12px;
            border-radius: 6px;
        }}

        QScrollBar::handle:vertical {{
            background-color: {self.text_muted};
            border-radius: 6px;
            min-height: 30px;
        }}

        QScrollBar::handle:vertical:hover {{
            background-color: {self.accent};
        }}

        QScrollBar:horizontal {{
            background-color: {self.bg_secondary};
            height: 12px;
            border-radius: 6px;
        }}

        QScrollBar::handle:horizontal {{
            background-color: {self.text_muted};
            border-radius: 6px;
            min-width: 30px;
        }}

        QScrollBar::handle:horizontal:hover {{
            background-color: {self.accent};
        }}

        QCheckBox {{
            color: {self.text_primary};
            spacing: 8px;
        }}

        QCheckBox::indicator {{
            width: 20px;
            height: 20px;
            border-radius: 4px;
            border: 2px solid {self.border};
            background-color: {self.bg_input};
        }}

        QCheckBox::indicator:checked {{
            background-color: {self.accent};
            border-color: {self.accent};
        }}

        QGroupBox {{
            color: {self.text_primary};
            border: 1px solid {self.border};
            border-radius: 12px;
            margin-top: 12px;
            padding-top: 16px;
            padding: 16px;
            font-weight: 600;
        }}

        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 16px;
            padding: 0 8px;
            color: {self.accent};
        }}

        QLabel {{
            color: {self.text_primary};
        }}

        QLabel#title {{
            font-size: 24px;
            font-weight: 700;
            color: {self.text_primary};
        }}

        QLabel#subtitle {{
            font-size: 14px;
            color: {self.text_secondary};
        }}

        QLabel#muted {{
            color: {self.text_muted};
        }}

        QFrame#card {{
            background-color: {self.bg_card};
            border-radius: 12px;
            border: 1px solid {self.border};
        }}

        QFrame#sidebar {{
            background-color: {self.bg_secondary};
            border-right: 1px solid {self.border};
        }}

        QListWidget {{
            background-color: {self.bg_card};
            color: {self.text_primary};
            border: 1px solid {self.border};
            border-radius: 12px;
            padding: 8px;
            outline: none;
        }}

        QListWidget::item {{
            padding: 12px;
            border-radius: 8px;
            margin: 2px 0;
        }}

        QListWidget::item:hover {{
            background-color: {self.bg_hover};
        }}

        QListWidget::item:selected {{
            background-color: {self.accent};
            color: white;
        }}

        QTabWidget::pane {{
            background-color: {self.bg_card};
            border: 1px solid {self.border};
            border-radius: 12px;
            top: -1px;
        }}

        QTabBar::tab {{
            background-color: {self.bg_secondary};
            color: {self.text_secondary};
            padding: 12px 24px;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
            margin-right: 4px;
        }}

        QTabBar::tab:hover {{
            background-color: {self.bg_hover};
            color: {self.text_primary};
        }}

        QTabBar::tab:selected {{
            background-color: {self.accent};
            color: white;
        }}

        QMenu {{
            background-color: {self.bg_card};
            color: {self.text_primary};
            border: 1px solid {self.border};
            border-radius: 8px;
            padding: 8px;
        }}

        QMenu::item {{
            padding: 10px 24px;
            border-radius: 6px;
        }}

        QMenu::item:hover {{
            background-color: {self.accent};
            color: white;
        }}

        QToolTip {{
            background-color: {self.bg_card};
            color: {self.text_primary};
            border: 1px solid {self.border};
            border-radius: 6px;
            padding: 8px;
        }}

        QSplitter::handle {{
            background-color: {self.border};
        }}

        QSplitter::handle:hover {{
            background-color: {self.accent};
        }}
        """

    def get_scrollbar_style(self) -> str:
        """Get scrollbar-specific stylesheet."""
        return """
        """
