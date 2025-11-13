"""
LangGraph Subtitle Translator

A refactored subtitle translation system using Builder and Chain of Responsibility patterns.
"""

__version__ = "2.0.0"
__author__ = "Your Name"

from .config import AppConstants, DefaultSettings, SettingsManager
from .core import TranslationRequest, SubtitleManager, TranslationExecutor
from .handlers import (
    TranslationHandler,
    ValidationHandler,
    ExecutionHandler,
    PersistenceHandler,
    LoggingHandler,
)
from .builders import TranslationPipelineBuilder
from .utils import LoggerUtils, FileUtils, PathManager

__all__ = [
    # Version
    "__version__",
    # Config
    "AppConstants",
    "DefaultSettings",
    "SettingsManager",
    # Core
    "TranslationRequest",
    "SubtitleManager",
    "TranslationExecutor",
    # Handlers
    "TranslationHandler",
    "ValidationHandler",
    "ExecutionHandler",
    "PersistenceHandler",
    "LoggingHandler",
    # Builders
    "TranslationPipelineBuilder",
    # Utils
    "LoggerUtils",
    "FileUtils",
    "PathManager",
]
