"""Logging handler - Step 4: Log results."""

import logging
from typing import Optional

from handlers.base_handler import TranslationHandler
from core.translation_request import TranslationRequest


class LoggingHandler(TranslationHandler):
    """
    Logs translation results.
    Fourth step in the chain.
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize logging handler.

        Args:
            logger: Logger instance
        """
        super().__init__()
        self.logger = logger or logging.getLogger(__name__)

    def handle(self, request: TranslationRequest) -> TranslationRequest:
        """
        Log translation results.

        Args:
            request: Translation request

        Returns:
            Request after logging
        """
        if request.success:
            self.logger.info(
                f"[{request.index}] 성공 "
                f"(시도: {request.attempt_count}, "
                f"토큰: {request.input_tokens}/{request.output_tokens})"
            )
        else:
            self.logger.error(
                f"[{request.index}] 실패: {request.error} "
                f"(시도: {request.attempt_count})"
            )

        # Proceed to next handler (if any)
        return self._call_next(request)
