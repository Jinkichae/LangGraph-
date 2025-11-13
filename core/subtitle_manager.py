"""Subtitle management following SRP (Single Responsibility Principle)."""

import copy
import threading
from typing import Dict, List, Optional
import pysrt
import logging

from utils.path_manager import PathManager


class SubtitleManager:
    """
    Manages subtitle files for multiple languages.
    Responsibilities:
    - Load and save subtitle files
    - Thread-safe subtitle updates
    - Context extraction
    """

    def __init__(
        self,
        path_manager: PathManager,
        lang_codes: List[str],
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize subtitle manager.

        Args:
            path_manager: Path manager instance
            lang_codes: List of language codes
            logger: Logger instance
        """
        self.path_manager = path_manager
        self.lang_codes = lang_codes
        self.logger = logger or logging.getLogger(__name__)

        # Load source subtitles
        source_path = path_manager.get_source_subtitle_path()
        self.ko_subs = pysrt.open(source_path, encoding="utf-8")
        self.ko_subs_len = len(self.ko_subs)

        # Initialize language subtitles
        self.lang_subs_dict = self._initialize_language_subs()
        self.subs_lock = threading.Lock()

    def _initialize_language_subs(self) -> Dict[str, pysrt.SubRipFile]:
        """
        Initialize subtitle objects for all languages.

        Returns:
            Dictionary mapping language codes to subtitle objects
        """
        lang_subs_dict = {}

        for lang_code in self.lang_codes:
            srt_path = self.path_manager.get_language_subtitle_path(lang_code)

            try:
                if self.path_manager.subtitle_file_exists(lang_code):
                    lang_subs_dict[lang_code] = pysrt.open(srt_path, encoding="utf-8")
                    self.logger.info(f"Loaded existing subtitles: {lang_code}")
                else:
                    # Create new subtitle file from Korean template
                    lang_subs_dict[lang_code] = copy.deepcopy(self.ko_subs)
                    self.logger.info(f"Created new subtitles from template: {lang_code}")
            except Exception as e:
                self.logger.error(f"Failed to initialize {lang_code} subtitles: {e}")
                lang_subs_dict[lang_code] = copy.deepcopy(self.ko_subs)

        return lang_subs_dict

    def get_text(self, index: int) -> str:
        """
        Get Korean text at index.

        Args:
            index: Subtitle index (1-based)

        Returns:
            Korean text or empty string
        """
        if 0 < index <= self.ko_subs_len:
            return self.ko_subs[index - 1].text
        return ""

    def get_context(self, index: int, context_size: int = 4) -> str:
        """
        Extract context from previous subtitles.

        Args:
            index: Current subtitle index (1-based)
            context_size: Number of previous items to include

        Returns:
            Context string with newline-separated previous subtitles
        """
        pool = [sub.text for sub in self.ko_subs]
        result = []
        idx = index - 1

        # Get previous items
        prev_indices = [
            idx - offset for offset in range(1, context_size + 1) if idx - offset >= 0
        ]
        prev_indices.reverse()

        for px in prev_indices:
            result.append(pool[px])

        # Fill remaining with next items if needed
        need = context_size - len(result)
        if need > 0:
            for j in range(idx + 1, len(pool)):
                if need <= 0:
                    break
                result.append(pool[j])
                need -= 1

        return "\n".join(result)

    def update_text(self, index: int, lang_code: str, text: str) -> bool:
        """
        Update subtitle text for a specific language (thread-safe).

        Args:
            index: Subtitle index (1-based)
            lang_code: Language code
            text: New text

        Returns:
            True if updated successfully
        """
        if not text or not text.strip():
            return False

        if lang_code not in self.lang_subs_dict:
            return False

        with self.subs_lock:
            try:
                subs = self.lang_subs_dict[lang_code]
                if 0 < index <= len(subs):
                    subs[index - 1].text = text
                    return True
            except Exception as e:
                self.logger.error(f"Failed to update {lang_code} at index {index}: {e}")

        return False

    def save_all(self):
        """Save all subtitle files to disk."""
        saved_count = 0
        error_count = 0

        with self.subs_lock:
            for lang_code, subs in self.lang_subs_dict.items():
                try:
                    srt_path = self.path_manager.get_language_subtitle_path(lang_code)
                    subs.save(srt_path, encoding="utf-8")
                    saved_count += 1
                except Exception as e:
                    error_count += 1
                    self.logger.error(f"Failed to save {lang_code}.srt: {e}")

        self.logger.info(
            f"Subtitle files saved: {saved_count} succeeded, {error_count} failed"
        )

    def get_failed_indices(self) -> List[int]:
        """
        Find indices with failed or missing translations.

        Returns:
            List of failed indices (1-based)
        """
        failed_indices = []

        with self.subs_lock:
            for i in range(self.ko_subs_len):
                ko_text = self.ko_subs[i].text.strip()
                if not ko_text:  # Skip empty source text
                    continue

                is_failed = False
                for lang_code in self.lang_codes:
                    if lang_code == "ko":  # Skip Korean
                        continue

                    if lang_code in self.lang_subs_dict:
                        translated_text = self.lang_subs_dict[lang_code][i].text.strip()
                        # Failed if empty or same as Korean
                        if not translated_text or translated_text == ko_text:
                            is_failed = True
                            break

                if is_failed:
                    failed_indices.append(i + 1)  # Convert to 1-based

        return failed_indices

    def __len__(self) -> int:
        """Return number of subtitles."""
        return self.ko_subs_len
