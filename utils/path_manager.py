"""Path management following DRY principle."""

import os
from typing import Optional

from config.constants import AppConstants


class PathManager:
    """Centralized path generation and management."""

    def __init__(self, base_dir: str):
        """
        Initialize path manager.

        Args:
            base_dir: Base directory for all paths
        """
        self.base_dir = os.path.normpath(base_dir)

    def get_source_subtitle_path(self) -> str:
        """Get path to source Korean subtitle file."""
        return os.path.join(self.base_dir, AppConstants.SOURCE_SUBTITLE_FILENAME)

    def get_language_subtitle_path(self, lang_code: str) -> str:
        """
        Get path to language-specific subtitle file.

        Args:
            lang_code: Language code (e.g., 'en', 'ja')

        Returns:
            Path to subtitle file
        """
        return os.path.join(self.base_dir, f"{lang_code}.srt")

    def get_index_file_path(self) -> str:
        """Get path to index file."""
        return os.path.join(self.base_dir, AppConstants.INDEX_FILENAME)

    def get_json_log_path(self) -> str:
        """Get path to JSON log file."""
        return os.path.join(self.base_dir, AppConstants.JSON_FILENAME)

    def subtitle_file_exists(self, lang_code: str) -> bool:
        """
        Check if subtitle file exists for language.

        Args:
            lang_code: Language code

        Returns:
            True if file exists
        """
        return os.path.exists(self.get_language_subtitle_path(lang_code))

    def source_subtitle_exists(self) -> bool:
        """Check if source subtitle file exists."""
        return os.path.exists(self.get_source_subtitle_path())

    def get_all_subtitle_paths(self, lang_codes: list) -> dict:
        """
        Get all subtitle file paths.

        Args:
            lang_codes: List of language codes

        Returns:
            Dictionary mapping language codes to file paths
        """
        return {
            lang_code: self.get_language_subtitle_path(lang_code)
            for lang_code in lang_codes
        }
