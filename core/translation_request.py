"""Translation request data object."""

from typing import Dict, List, Optional


class TranslationRequest:
    """
    Data object representing a translation request.
    Used in the Chain of Responsibility pattern.
    """

    def __init__(
        self,
        index: int,
        ko_text: str,
        context: str,
        target_langs: List[str],
    ):
        """
        Initialize translation request.

        Args:
            index: Subtitle index (1-based)
            ko_text: Korean text to translate
            context: Context for translation
            target_langs: List of target language codes
        """
        self.index = index
        self.ko_text = ko_text
        self.context = context
        self.target_langs = target_langs

        # Results
        self.translations: Dict[str, str] = {}
        self.success = False
        self.error: Optional[str] = None

        # Metadata
        self.attempt_count = 0
        self.input_tokens = 0
        self.output_tokens = 0

    def mark_success(self, translations: Dict[str, str]):
        """
        Mark request as successful.

        Args:
            translations: Dictionary of language code to translated text
        """
        self.success = True
        self.translations = translations
        self.error = None

    def mark_failure(self, error: str):
        """
        Mark request as failed.

        Args:
            error: Error message
        """
        self.success = False
        self.error = error

    def increment_attempt(self):
        """Increment attempt counter."""
        self.attempt_count += 1

    def set_token_usage(self, input_tokens: int, output_tokens: int):
        """
        Set token usage.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
        """
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens

    def is_valid(self) -> bool:
        """
        Check if request is valid for processing.

        Returns:
            True if request has valid data
        """
        return (
            bool(self.ko_text and self.ko_text.strip())
            and bool(self.target_langs)
            and self.index > 0
        )

    def __repr__(self) -> str:
        """String representation."""
        status = "SUCCESS" if self.success else "FAILED" if self.error else "PENDING"
        return f"TranslationRequest(index={self.index}, status={status}, attempts={self.attempt_count})"
