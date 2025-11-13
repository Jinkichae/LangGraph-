"""Settings management following SOLID principles."""

from typing import List, Optional


class DefaultSettings:
    """Default settings as class variables for centralized management."""

    # Translation settings
    DEFAULT_TEMPERATURE = 0.1
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_RETRY_DELAY = 1.0
    DEFAULT_CONTEXT_SIZE = 4

    # Thread pool settings
    DEFAULT_WORKER_COUNT = 6
    DEFAULT_BATCH_SIZE = 12
    DEFAULT_SAVE_INTERVAL = 30

    # Timeout settings
    DEFAULT_TIMEOUT = 90.0
    DEFAULT_BATCH_TIMEOUT = 300
    DEFAULT_RESULT_TIMEOUT = 15

    # Agent settings
    DEFAULT_RECURSION_LIMIT = 10
    DEFAULT_MAX_EXECUTION_TIME = 60
    DEFAULT_MAX_ITERATIONS = 3

    # Retry settings
    DEFAULT_AUTO_RETRY_COUNT = 2
    DEFAULT_RETRY_SLEEP = 2


class SettingsManager:
    """Manages application settings with validation."""

    def __init__(
        self,
        groq_api_key: str,
        lang_codes_str: str,
        srt_dir: str,
        model_priority_index: int = 0,
        temperature: float = DefaultSettings.DEFAULT_TEMPERATURE,
        max_retries: int = DefaultSettings.DEFAULT_MAX_RETRIES,
        worker_count: int = DefaultSettings.DEFAULT_WORKER_COUNT,
        batch_size: int = DefaultSettings.DEFAULT_BATCH_SIZE,
        save_interval: int = DefaultSettings.DEFAULT_SAVE_INTERVAL,
        context_size: int = DefaultSettings.DEFAULT_CONTEXT_SIZE,
    ):
        """Initialize settings with validation."""
        self._validate_inputs(groq_api_key, lang_codes_str, srt_dir)

        self.groq_api_key = groq_api_key
        self.lang_codes_str = lang_codes_str
        self.srt_dir = srt_dir
        self.model_priority_index = model_priority_index
        self.temperature = temperature
        self.max_retries = max_retries
        self.worker_count = worker_count
        self.batch_size = batch_size
        self.save_interval = save_interval
        self.context_size = context_size

        # Parse language codes
        self.lang_codes_list = [code.strip() for code in lang_codes_str.split(",")]

    def _validate_inputs(self, api_key: str, lang_codes: str, srt_dir: str):
        """Validate required inputs."""
        if not api_key or not api_key.strip():
            raise ValueError("GROQ API key is required")

        if not lang_codes or not lang_codes.strip():
            raise ValueError("Language codes are required")

        if not srt_dir or not srt_dir.strip():
            raise ValueError("SRT directory is required")

    def get_lang_codes_list(self) -> List[str]:
        """Get list of language codes."""
        return self.lang_codes_list

    def get_recursion_limit(self) -> int:
        """Get recursion limit for agent."""
        return DefaultSettings.DEFAULT_RECURSION_LIMIT

    def get_max_execution_time(self) -> int:
        """Get max execution time for agent."""
        return DefaultSettings.DEFAULT_MAX_EXECUTION_TIME

    def get_max_iterations(self) -> int:
        """Get max iterations for agent."""
        return DefaultSettings.DEFAULT_MAX_ITERATIONS

    def get_timeout(self) -> float:
        """Get timeout for translation."""
        return DefaultSettings.DEFAULT_TIMEOUT

    def get_batch_timeout(self) -> int:
        """Get batch timeout."""
        return DefaultSettings.DEFAULT_BATCH_TIMEOUT

    def get_result_timeout(self) -> int:
        """Get result timeout."""
        return DefaultSettings.DEFAULT_RESULT_TIMEOUT

    def get_retry_delay(self, attempt: int) -> float:
        """Calculate retry delay based on attempt number."""
        return DefaultSettings.DEFAULT_RETRY_DELAY + attempt * 0.5

    def __repr__(self) -> str:
        """String representation of settings."""
        return (
            f"SettingsManager("
            f"lang_codes={self.lang_codes_list}, "
            f"model_index={self.model_priority_index}, "
            f"workers={self.worker_count}, "
            f"batch={self.batch_size})"
        )
