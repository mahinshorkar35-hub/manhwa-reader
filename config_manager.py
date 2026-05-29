"""
Configuration Manager Module
Handles application settings and encrypted API key storage.
"""

import os
import json
import base64
import logging
from pathlib import Path
from typing import Dict, Optional, Any
from dataclasses import dataclass, asdict
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import appdirs

logger = logging.getLogger(__name__)


@dataclass
class AppSettings:
    """Application settings data class."""
    # API Keys (will be stored encrypted)
    openai_api_key: str = ""
    gemini_api_key: str = ""
    elevenlabs_api_key: str = ""

    # AI Provider settings
    vision_provider: str = "openai"  # openai, gemini, ollama
    vision_model: str = "gpt-4o"  # gpt-4o, gpt-4o-mini, etc.
    tts_provider: str = "edge"  # elevenlabs, edge, kokoro, pyttsx3
    tts_voice: str = "en-US-AriaNeural"
    ollama_model: str = "llava"
    ollama_url: str = "http://localhost:11434"

    # Processing settings
    extraction_level: str = "medium"  # low, medium, high
    summary_style: str = "dramatic"  # dramatic, casual, anime, concise
    target_video_length: int = 5  # minutes
    max_panels: int = 20
    include_page_numbers: bool = True
    include_chapter_titles: bool = True

    # Output settings
    output_directory: str = ""
    video_resolution: str = "720p"  # 720p, 1080p
    video_fps: int = 24
    video_bitrate: str = "5000k"
    transition_type: str = "fade"
    ken_burns_effect: bool = True
    text_overlay: bool = True

    # UI settings
    dark_mode: bool = True
    sidebar_width: int = 250
    window_width: int = 1400
    window_height: int = 900

    # Advanced
    log_level: str = "INFO"
    auto_update_check: bool = True
    preserve_temp_files: bool = False


class ConfigManager:
    """Manages application configuration and encrypted API key storage."""

    APP_NAME = "MangaRecap"
    APP_AUTHOR = "MangaRecapTeam"
    CONFIG_FILE = "settings.json"
    SALT_FILE = "salt.key"

    def __init__(self):
        self.app_dir = Path(appdirs.user_data_dir(self.APP_NAME, self.APP_AUTHOR))
        self.app_dir.mkdir(parents=True, exist_ok=True)

        self.config_path = self.app_dir / self.CONFIG_FILE
        self.salt_path = self.app_dir / self.SALT_FILE

        self._salt = None
        self._cipher = None
        self._settings = AppSettings()

        self._init_encryption()
        self.load()

    def _init_encryption(self):
        """Initialize encryption for API keys."""
        try:
            if self.salt_path.exists():
                self._salt = self.salt_path.read_bytes()
            else:
                self._salt = os.urandom(16)
                self.salt_path.write_bytes(self._salt)

            # Derive key from machine-specific identifier + salt
            machine_id = self._get_machine_id()
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=self._salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(machine_id.encode()))
            self._cipher = Fernet(key)

        except Exception as e:
            logger.error(f"Encryption initialization failed: {e}")
            # Use a simple fallback - still better than plain text
            self._cipher = None

    def _get_machine_id(self) -> str:
        """Get a machine-specific identifier for key derivation."""
        try:
            import platform
            import uuid

            # Combine machine-specific values
            machine_id = platform.node()  # Computer name
            if not machine_id:
                # Fallback: use a hash of the user's home directory
                machine_id = str(uuid.uuid5(uuid.NAMESPACE_URL, str(Path.home())))
            return machine_id
        except Exception:
            return "manga_recap_default_key"

    def _encrypt(self, value: str) -> str:
        """Encrypt a string value."""
        if not value:
            return ""
        if self._cipher is None:
            # Fallback: base64 encode (obfuscation only)
            return base64.b64encode(value.encode()).decode()
        return self._cipher.encrypt(value.encode()).decode()

    def _decrypt(self, value: str) -> str:
        """Decrypt a string value."""
        if not value:
            return ""
        if self._cipher is None:
            try:
                return base64.b64decode(value.encode()).decode()
            except Exception:
                return value
        try:
            return self._cipher.decrypt(value.encode()).decode()
        except Exception:
            # If decryption fails, return as-is (might be unencrypted legacy value)
            return value

    def load(self):
        """Load settings from disk."""
        try:
            if self.config_path.exists():
                data = json.loads(self.config_path.read_text())

                # Decrypt API keys
                for key in ['openai_api_key', 'gemini_api_key', 'elevenlabs_api_key']:
                    if key in data and data[key]:
                        data[key] = self._decrypt(data[key])

                # Update settings with loaded values
                for key, value in data.items():
                    if hasattr(self._settings, key):
                        setattr(self._settings, key, value)

                logger.info("Settings loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load settings: {e}. Using defaults.")
            self._settings = AppSettings()

    def save(self):
        """Save settings to disk."""
        try:
            data = asdict(self._settings)

            # Encrypt API keys before saving
            for key in ['openai_api_key', 'gemini_api_key', 'elevenlabs_api_key']:
                if key in data and data[key]:
                    data[key] = self._encrypt(data[key])

            self.config_path.write_text(json.dumps(data, indent=2))
            logger.info("Settings saved successfully")

        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            raise

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        return getattr(self._settings, key, default)

    def set(self, key: str, value: Any):
        """Set a setting value."""
        if hasattr(self._settings, key):
            setattr(self._settings, key, value)
        else:
            logger.warning(f"Unknown setting: {key}")

    def get_settings(self) -> AppSettings:
        """Get the full settings object."""
        return self._settings

    def update_settings(self, settings: Dict[str, Any]):
        """Update multiple settings at once."""
        for key, value in settings.items():
            self.set(key, value)

    def get_api_key(self, provider: str) -> str:
        """Get API key for a specific provider."""
        key_map = {
            'openai': 'openai_api_key',
            'gemini': 'gemini_api_key',
            'elevenlabs': 'elevenlabs_api_key',
        }
        setting_key = key_map.get(provider)
        if setting_key:
            return self.get(setting_key, "")
        return ""

    def set_api_key(self, provider: str, key: str):
        """Set API key for a specific provider."""
        key_map = {
            'openai': 'openai_api_key',
            'gemini': 'gemini_api_key',
            'elevenlabs': 'elevenlabs_api_key',
        }
        setting_key = key_map.get(provider)
        if setting_key:
            self.set(setting_key, key)

    def get_output_dir(self) -> str:
        """Get the output directory, creating if needed."""
        output_dir = self.get('output_directory', '')
        if not output_dir:
            output_dir = str(Path.home() / "MangaRecaps")
            self.set('output_directory', output_dir)
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        return output_dir

    def get_temp_dir(self) -> str:
        """Get temporary working directory."""
        temp_dir = self.app_dir / "temp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        return str(temp_dir)

    def get_history_file(self) -> str:
        """Get path to history file."""
        return str(self.app_dir / "history.json")

    def reset_to_defaults(self):
        """Reset all settings to defaults."""
        self._settings = AppSettings()
        self.save()
        logger.info("Settings reset to defaults")
