"""Persistence handler - Step 3: Save translation results."""

import logging
from typing import Optional

from handlers.base_handler import TranslationHandler
from core.translation_request import TranslationRequest
from core.subtitle_manager import SubtitleManager


class PersistenceHandler(TranslationHandler):
    """
    Saves translation results to subtitle manager.
    Third step in the chain.
    """

    def __init__(
        self,
        subtitle_manager: SubtitleManager,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize persistence handler.

        Args:
            subtitle_manager: Subtitle manager instance
            logger: Logger instance
        """
        super().__init__()
        self.subtitle_manager = subtitle_manager
        self.logger = logger or logging.getLogger(__name__)

    def handle(self, request: TranslationRequest) -> TranslationRequest:
        """
        Save translation results.

        Args:
            request: Translation request

        Returns:
            Request after persistence
        """
        # Only save if successful
        if request.success and request.translations:
            for lang_code, text in request.translations.items():
                try:
                    success = self.subtitle_manager.update_text(
                        request.index, lang_code, text
                    )
                    if not success:
                        self.logger.warning(
                            f"[인덱스 {request.index}] {lang_code} 저장 실패"
                        )
                except Exception as e:
                    self.logger.error(
                        f"[인덱스 {request.index}] {lang_code} 저장 중 오류: {e}"
                    )

        # Proceed to next handler
        return self._call_next(request)
