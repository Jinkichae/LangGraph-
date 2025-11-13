"""Execution handler - Step 2: Translation execution with retry logic."""

import time
import logging
from typing import Optional

from handlers.base_handler import TranslationHandler
from core.translation_request import TranslationRequest
from core.translation_executor import TranslationExecutor


class ExecutionHandler(TranslationHandler):
    """
    Executes translation with retry logic.
    Second step in the chain.
    """

    def __init__(
        self,
        executor: TranslationExecutor,
        max_attempts: int = 3,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize execution handler.

        Args:
            executor: Translation executor instance
            max_attempts: Maximum number of retry attempts
            logger: Logger instance
        """
        super().__init__()
        self.executor = executor
        self.max_attempts = max_attempts
        self.logger = logger or logging.getLogger(__name__)

    def handle(self, request: TranslationRequest) -> TranslationRequest:
        """
        Execute translation with retry logic.

        Args:
            request: Translation request

        Returns:
            Request with translation results
        """
        # Skip if previous handler marked as failed
        if request.error:
            return self._call_next(request)

        # Retry loop
        while request.attempt_count < self.max_attempts:
            request.increment_attempt()

            try:
                # Execute translation
                success, translations, input_t, output_t = self.executor.execute_sync(
                    request.ko_text, request.context, request.target_langs
                )

                # Set token usage
                request.set_token_usage(input_t, output_t)

                if success and translations:
                    request.mark_success(translations)
                    break
                else:
                    # Retry with delay
                    if request.attempt_count < self.max_attempts:
                        delay = 1.0 + request.attempt_count * 0.5
                        time.sleep(delay)

            except Exception as e:
                error_msg = f"실행 오류: {str(e)}"
                self.logger.error(
                    f"[인덱스 {request.index}] 시도 {request.attempt_count}/{self.max_attempts}: {error_msg}"
                )

                # Mark as failed on last attempt
                if request.attempt_count >= self.max_attempts:
                    request.mark_failure(error_msg)
                else:
                    # Retry with delay
                    delay = 1.0 + request.attempt_count * 0.5
                    time.sleep(delay)

        # Mark as failed if not successful after all attempts
        if not request.success:
            request.mark_failure(f"최대 재시도 횟수 초과 ({self.max_attempts})")

        # Proceed to next handler
        return self._call_next(request)
