"""Base handler for Chain of Responsibility pattern."""

from abc import ABC, abstractmethod
from typing import Optional

from core.translation_request import TranslationRequest


class TranslationHandler(ABC):
    """
    Base class for translation request handlers.
    Implements the Chain of Responsibility pattern.
    """

    def __init__(self):
        """Initialize handler."""
        self._next_handler: Optional[TranslationHandler] = None

    def set_next(self, handler: "TranslationHandler") -> "TranslationHandler":
        """
        Set the next handler in the chain.

        Args:
            handler: Next handler

        Returns:
            The next handler (for chaining)
        """
        self._next_handler = handler
        return handler

    @abstractmethod
    def handle(self, request: TranslationRequest) -> TranslationRequest:
        """
        Handle the translation request.

        Args:
            request: Translation request

        Returns:
            Modified translation request
        """
        pass

    def _call_next(self, request: TranslationRequest) -> TranslationRequest:
        """
        Call the next handler in the chain.

        Args:
            request: Translation request

        Returns:
            Translation request from next handler
        """
        if self._next_handler:
            return self._next_handler.handle(request)
        return request
