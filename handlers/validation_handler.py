"""Validation handler - Step 1: Request validation."""

from handlers.base_handler import TranslationHandler
from core.translation_request import TranslationRequest


class ValidationHandler(TranslationHandler):
    """
    Validates translation requests before processing.
    First step in the chain.
    """

    def handle(self, request: TranslationRequest) -> TranslationRequest:
        """
        Validate the translation request.

        Args:
            request: Translation request

        Returns:
            Validated request (or request with error)
        """
        # Check if text is empty
        if not request.ko_text or not request.ko_text.strip():
            request.mark_failure("빈 텍스트")
            return request

        # Check if target languages are specified
        if not request.target_langs:
            request.mark_failure("언어 코드 없음")
            return request

        # Check if index is valid
        if request.index <= 0:
            request.mark_failure("잘못된 인덱스")
            return request

        # Validation passed, proceed to next handler
        return self._call_next(request)
