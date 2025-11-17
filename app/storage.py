"""
Persistent Storage System
Handles saving and loading of fixtures, scenes, and settings
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class Storage:
    """JSON-based persistent storage"""

    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize storage

        Args:
            config_dir: Directory for configuration files (default: <project_root>/config)
        """
        if config_dir is None:
            # Use config directory relative to project root
            project_root = Path(__file__).parent.parent
            config_dir = project_root / "config"

        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self.fixtures_file = self.config_dir / "fixtures.json"
        self.scenes_file = self.config_dir / "scenes.json"
        self.settings_file = self.config_dir / "settings.json"

    def save_fixtures(self, data: dict) -> bool:
        """
        Save fixtures to JSON

        Args:
            data: Fixture data dictionary

        Returns:
            True if successful
        """
        try:
            with open(self.fixtures_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Fixtures saved to {self.fixtures_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving fixtures: {e}")
            return False

    def load_fixtures(self) -> Optional[dict]:
        """
        Load fixtures from JSON

        Returns:
            Fixture data dictionary or None if error
        """
        if not self.fixtures_file.exists():
            logger.info("No fixtures file found, starting with empty fixtures")
            return {"fixtures": []}

        try:
            with open(self.fixtures_file, 'r') as f:
                data = json.load(f)
            logger.info(f"Fixtures loaded from {self.fixtures_file}")
            return data
        except Exception as e:
            logger.error(f"Error loading fixtures: {e}")
            return None

    def save_scenes(self, data: dict) -> bool:
        """
        Save scenes to JSON

        Args:
            data: Scene data dictionary

        Returns:
            True if successful
        """
        try:
            with open(self.scenes_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Scenes saved to {self.scenes_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving scenes: {e}")
            return False

    def load_scenes(self) -> Optional[dict]:
        """
        Load scenes from JSON

        Returns:
            Scene data dictionary or None if error
        """
        if not self.scenes_file.exists():
            logger.info("No scenes file found, starting with empty scenes")
            return {"scenes": []}

        try:
            with open(self.scenes_file, 'r') as f:
                data = json.load(f)
            logger.info(f"Scenes loaded from {self.scenes_file}")
            return data
        except Exception as e:
            logger.error(f"Error loading scenes: {e}")
            return None

    def save_settings(self, settings: dict) -> bool:
        """
        Save application settings

        Args:
            settings: Settings dictionary

        Returns:
            True if successful
        """
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
            logger.info(f"Settings saved to {self.settings_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            return False

    def load_settings(self) -> dict:
        """
        Load application settings

        Returns:
            Settings dictionary
        """
        default_settings = {
            "dmx_port": "/dev/ttyUSB0",
            "dmx_baudrate": 250000,
            "oled_address": "0x3C",
            "oled_type": "ssd1306",
            "ads1115_address": 0x48,
            "log_level": "INFO",
            "encoder_pins": {
                "encoder_1": {"a": 15, "b": 18, "btn": 17},
                "encoder_2": {"a": 22, "b": 23, "btn": 24},
                "encoder_3": {"a": 25, "b": 8, "btn": 7},
                "encoder_4": {"a": 12, "b": 16, "btn": 20}
            }
        }

        if not self.settings_file.exists():
            logger.info("No settings file found, using defaults")
            self.save_settings(default_settings)
            return default_settings

        try:
            with open(self.settings_file, 'r') as f:
                settings = json.load(f)
            logger.info(f"Settings loaded from {self.settings_file}")

            # Merge with defaults (in case new settings were added)
            for key, value in default_settings.items():
                if key not in settings:
                    settings[key] = value

            return settings
        except Exception as e:
            logger.error(f"Error loading settings: {e}, using defaults")
            return default_settings

    def export_all(self, export_path: str) -> bool:
        """
        Export all configuration to a single file

        Args:
            export_path: Path to export file

        Returns:
            True if successful
        """
        try:
            export_data = {
                "fixtures": self.load_fixtures(),
                "scenes": self.load_scenes(),
                "settings": self.load_settings()
            }

            with open(export_path, 'w') as f:
                json.dump(export_data, f, indent=2)

            logger.info(f"Configuration exported to {export_path}")
            return True
        except Exception as e:
            logger.error(f"Error exporting configuration: {e}")
            return False

    def import_all(self, import_path: str) -> bool:
        """
        Import all configuration from a file

        Args:
            import_path: Path to import file

        Returns:
            True if successful
        """
        try:
            with open(import_path, 'r') as f:
                import_data = json.load(f)

            if "fixtures" in import_data:
                self.save_fixtures(import_data["fixtures"])

            if "scenes" in import_data:
                self.save_scenes(import_data["scenes"])

            if "settings" in import_data:
                self.save_settings(import_data["settings"])

            logger.info(f"Configuration imported from {import_path}")
            return True
        except Exception as e:
            logger.error(f"Error importing configuration: {e}")
            return False

    def backup(self, backup_dir: Optional[str] = None) -> Optional[str]:
        """
        Create a backup of all configuration files

        Args:
            backup_dir: Directory for backup (default: config/backups)

        Returns:
            Path to backup file or None if error
        """
        import datetime

        if backup_dir is None:
            backup_dir = self.config_dir / "backups"
        else:
            backup_dir = Path(backup_dir)

        backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"dmx_backup_{timestamp}.json"

        if self.export_all(str(backup_file)):
            logger.info(f"Backup created: {backup_file}")
            return str(backup_file)
        else:
            return None
