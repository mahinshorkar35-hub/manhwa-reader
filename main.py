"""
MangaRecap - Main Application Entry Point
A professional desktop application for converting manga PDFs into narrated recap videos.
"""

import sys
import os
import logging
from pathlib import Path

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFontDatabase, QFont

from core.config_manager import ConfigManager
from gui.styles import AppTheme
from gui.main_window import MainWindow


def setup_logging():
    """Configure application logging."""
    config = ConfigManager()
    log_level = getattr(logging, config.get('log_level', 'INFO').upper(), logging.INFO)

    log_dir = Path(config.app_dir) / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / "manga_recap.log"

    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(str(log_file), encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Suppress noisy third-party logs
    logging.getLogger('PIL').setLevel(logging.WARNING)
    logging.getLogger('moviepy').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)

    return logging.getLogger(__name__)


def setup_app():
    """Configure the QApplication."""
    # Enable high DPI scaling
    os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'
    os.environ['QT_ENABLE_HIGHDPI_SCALING'] = '1'

    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # Set application metadata
    app.setApplicationName("MangaRecap")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("MangaRecapTeam")

    # Load config and apply theme
    config = ConfigManager()
    theme = AppTheme(dark_mode=config.get('dark_mode', True))
    app.setPalette(theme.get_palette())
    app.setStyleSheet(theme.get_stylesheet())

    # Set default font
    font = QFont("Segoe UI", 10)
    if "Segoe UI" not in QFontDatabase.families():
        font = QFont("Arial", 10)
    app.setFont(font)

    return app


def main():
    """Main entry point."""
    logger = setup_logging()
    logger.info("=" * 50)
    logger.info("MangaRecap v1.0.0 Starting...")
    logger.info("=" * 50)

    try:
        app = setup_app()

        # Create and show main window
        window = MainWindow()
        window.show()

        logger.info("Application started successfully")

        # Run event loop
        sys.exit(app.exec())

    except Exception as e:
        logger.critical(f"Application failed to start: {e}", exc_info=True)
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(None, "Fatal Error",
                            f"Application failed to start:\n\n{str(e)}\n\n"
                            f"Check logs for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
