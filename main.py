"""Main application orchestrating the translation workflow."""

import os
import sys
import time
import logging
import warnings
import asyncio
import threading
import concurrent.futures
from typing import List, Optional
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv

# Local imports
from config.constants import AppConstants
from config.settings import SettingsManager, DefaultSettings
from utils.logger_utils import LoggerUtils
from utils.file_utils import FileUtils
from utils.path_manager import PathManager
from core.translation_request import TranslationRequest
from core.subtitle_manager import SubtitleManager
from core.translation_executor import TranslationExecutor
from builders.pipeline_builder import TranslationPipelineBuilder
from langchain.tools import StructuredTool


# Suppress warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", message=".*Event loop is closed.*")
warnings.filterwarnings("ignore", message=".*coroutine.*was never awaited.*")
warnings.filterwarnings("ignore", message=".*Task exception was never retrieved.*")
warnings.filterwarnings("ignore", message=".*Importing verbose from langchain.*")

# Suppress asyncio debug warnings
import logging
logging.getLogger("asyncio").setLevel(logging.CRITICAL)

# Windows event loop policy
if os.name == "nt":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Set custom asyncio exception handler to suppress event loop closure errors
def asyncio_exception_handler(loop, context):
    """Suppress event loop closure errors."""
    exception = context.get("exception")
    if exception:
        error_msg = str(exception).lower()
        # Suppress specific errors
        if any(msg in error_msg for msg in ["event loop is closed", "connection_lost"]):
            return
    # For other exceptions, use default behavior but suppress output
    pass


class TranslationOrchestrator:
    """
    Main orchestrator for the translation workflow.
    Coordinates all components and manages the translation process.
    """

    def __init__(self, settings: SettingsManager):
        """
        Initialize orchestrator.

        Args:
            settings: Settings manager instance
        """
        self.settings = settings
        self.logger = LoggerUtils.setup_logger("TranslationOrchestrator")
        LoggerUtils.suppress_noisy_loggers()

        # Initialize components
        self.path_manager = PathManager(settings.srt_dir)
        self.subtitle_manager = SubtitleManager(
            self.path_manager, settings.lang_codes_list, self.logger
        )

        # Get model name
        try:
            self.model_name = AppConstants.MODEL_PRIORITY_LIST[
                settings.model_priority_index
            ]
        except IndexError:
            self.model_name = AppConstants.MODEL_PRIORITY_LIST[0]
            self.logger.warning(
                f"Invalid model index, using default: {self.model_name}"
            )

        # Create executor
        self.executor = TranslationExecutor(settings, self.model_name, self.logger)

        # Build pipeline
        self.pipeline = (
            TranslationPipelineBuilder()
            .add_validation()
            .add_execution(self.executor, settings.max_retries, self.logger)
            .add_persistence(self.subtitle_manager, self.logger)
            .add_logging(self.logger)
            .build()
        )

        # Statistics
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.stats_lock = threading.Lock()

        # Shutdown flag
        self._shutdown_event = threading.Event()

        self.logger.info(f"Initialized with model: {self.model_name}")
        self.logger.info(f"Languages: {settings.lang_codes_list}")
        self.logger.info(f"Total subtitles: {len(self.subtitle_manager)}")

    def load_progress(self) -> int:
        """
        Load progress from index file.

        NOTE: Always returns 1 to start from beginning.
        Progress loading feature has been disabled.

        Returns:
            Starting index (always 1)
        """
        return 1

    def save_progress(self, index: int):
        """
        Save progress to index file.

        Args:
            index: Current index
        """
        try:
            with self.stats_lock:
                total_input = self.total_input_tokens
                total_output = self.total_output_tokens

            data = {
                "lang_codes_str": ",".join(self.settings.lang_codes_list),
                "a_index": index,
                "model_name": self.model_name,
                "total_input_tokens": total_input,
                "total_output_tokens": total_output,
            }

            # Save to index file
            index_path = self.path_manager.get_index_file_path()
            FileUtils.write_json_file(index_path, data)

            # Append to JSON log
            json_log_path = self.path_manager.get_json_log_path()
            FileUtils.append_to_json_list(json_log_path, data)

        except Exception as e:
            self.logger.error(f"Failed to save progress: {e}")

    def process_request(self, index: int) -> bool:
        """
        Process a single translation request through the pipeline.

        Args:
            index: Subtitle index (1-based)

        Returns:
            True if successful
        """
        if self._shutdown_event.is_set():
            return False

        # Create request
        ko_text = self.subtitle_manager.get_text(index)
        context = self.subtitle_manager.get_context(index, self.settings.context_size)

        request = TranslationRequest(
            index=index,
            ko_text=ko_text,
            context=context,
            target_langs=self.settings.lang_codes_list,
        )

        # Process through pipeline
        result = self.pipeline.handle(request)

        # Update token statistics
        if result.input_tokens > 0 or result.output_tokens > 0:
            with self.stats_lock:
                self.total_input_tokens += result.input_tokens
                self.total_output_tokens += result.output_tokens

        return result.success

    def run_batch_translation(
        self,
        start_index: Optional[int] = None,
        worker_count: Optional[int] = None,
        batch_size: Optional[int] = None,
        save_interval: Optional[int] = None,
    ):
        """
        Run batch translation with thread pool.

        Args:
            start_index: Starting index (default: load from file)
            worker_count: Number of workers (default: from settings)
            batch_size: Batch size (default: from settings)
            save_interval: Save interval (default: from settings)
        """
        # Use defaults from settings
        start_index = start_index or self.load_progress()
        worker_count = worker_count or self.settings.worker_count
        batch_size = batch_size or self.settings.batch_size
        save_interval = save_interval or self.settings.save_interval

        # Validate start index
        total_subs = len(self.subtitle_manager)
        if not (1 <= start_index <= total_subs):
            self.logger.warning(f"Invalid start index: {start_index}, using 1")
            start_index = 1

        self.logger.info(
            f"Starting batch translation from index {start_index}/{total_subs}: "
            f"workers={worker_count}, batch={batch_size}, save_interval={save_interval}"
        )

        try:
            processed_count = 0
            success_count = 0
            failed_indices = []

            with concurrent.futures.ThreadPoolExecutor(
                max_workers=worker_count, thread_name_prefix="Translator"
            ) as executor:

                current_index = start_index

                while current_index <= total_subs and not self._shutdown_event.is_set():
                    # Create batch
                    batch = list(
                        range(
                            current_index,
                            min(current_index + batch_size, total_subs + 1),
                        )
                    )

                    self.logger.info(f"Processing batch: {batch[0]}-{batch[-1]} ({len(batch)} items)")

                    # Submit batch
                    future_to_index = {
                        executor.submit(self.process_request, idx): idx for idx in batch
                    }

                    # Collect results
                    for future in concurrent.futures.as_completed(
                        future_to_index, timeout=self.settings.get_batch_timeout()
                    ):
                        if self._shutdown_event.is_set():
                            break

                        idx = future_to_index[future]
                        try:
                            success = future.result(
                                timeout=self.settings.get_result_timeout()
                            )
                            if success:
                                success_count += 1
                            else:
                                failed_indices.append(idx)
                                self.logger.warning(f"Index {idx} failed")

                        except concurrent.futures.TimeoutError:
                            failed_indices.append(idx)
                            self.logger.error(f"Index {idx} timeout")
                            future.cancel()
                        except Exception as e:
                            failed_indices.append(idx)
                            self.logger.error(f"Index {idx} error: {e}")

                        processed_count += 1

                        # Progress logging
                        if processed_count % 5 == 0:
                            with self.stats_lock:
                                ti = self.total_input_tokens
                                to = self.total_output_tokens

                            self.logger.info(
                                f"Progress: {processed_count}/{total_subs} "
                                f"(success: {success_count}, failed: {len(failed_indices)}) "
                                f"Tokens: {ti}/{to}"
                            )

                    # Periodic save
                    if processed_count % save_interval == 0:
                        self.save_progress(current_index + batch_size)
                        self.logger.info(
                            f"Saving progress at {processed_count} items..."
                        )
                        self.subtitle_manager.save_all()

                    current_index += batch_size
                    time.sleep(0.1)  # Brief pause between batches

            # Retry failed items
            retry_success = 0
            if failed_indices and not self._shutdown_event.is_set():
                self.logger.info(f"Retrying {len(failed_indices)} failed items...")
                retry_success = self._retry_failed_items(failed_indices)

            # Final save
            self.save_progress(total_subs)
            self.subtitle_manager.save_all()

            # Print statistics
            self._print_statistics(
                total_subs,
                success_count,
                retry_success,
                len(failed_indices) - retry_success,
            )

        except KeyboardInterrupt:
            self.logger.info("Interrupted by user")
            self._shutdown_event.set()
        except Exception as e:
            self.logger.error(f"Batch translation error: {e}")
            self._shutdown_event.set()
        finally:
            self.logger.info("Cleaning up...")
            self._shutdown_event.set()
            time.sleep(1)

    def _retry_failed_items(
        self, failed_indices: List[int], max_retries: int = 2
    ) -> int:
        """
        Retry failed items.

        Args:
            failed_indices: List of failed indices
            max_retries: Maximum retry rounds

        Returns:
            Number of successful retries
        """
        retry_success = 0
        remaining = failed_indices.copy()

        for retry_round in range(max_retries):
            if not remaining or self._shutdown_event.is_set():
                break

            self.logger.info(
                f"Retry round {retry_round + 1}/{max_retries}: {len(remaining)} items"
            )
            current_failed = remaining.copy()
            remaining = []

            for idx in current_failed:
                if self._shutdown_event.is_set():
                    break

                try:
                    self.logger.info(f"Retrying index {idx}")
                    success = self.process_request(idx)

                    if success:
                        retry_success += 1
                        self.logger.info(f"Retry success: index {idx}")
                    else:
                        remaining.append(idx)
                        self.logger.warning(f"Retry failed: index {idx}")

                    time.sleep(2)  # Delay between retries

                except Exception as e:
                    remaining.append(idx)
                    self.logger.error(f"Retry error - index {idx}: {e}")

            # Save after each retry round
            if retry_success > 0:
                self.logger.info("Saving after retry round...")
                self.subtitle_manager.save_all()

            if remaining and retry_round < max_retries - 1:
                time.sleep(3)  # Delay before next round

        if remaining:
            self.logger.warning(f"Final failed items: {remaining}")

        return retry_success

    def manual_retry_failed(self, max_retries: int = 3):
        """
        Manually retry all failed items found in subtitle files.

        Args:
            max_retries: Maximum retry attempts per item
        """
        self.logger.info("Searching for failed items...")
        failed_indices = self.subtitle_manager.get_failed_indices()

        if not failed_indices:
            self.logger.info("No failed items found")
            return

        self.logger.info(f"Found {len(failed_indices)} failed items")
        retry_success = self._retry_failed_items(failed_indices, max_retries)

        self.logger.info(
            f"Manual retry completed: {retry_success}/{len(failed_indices)} succeeded"
        )

    def _print_statistics(
        self, total: int, initial_success: int, retry_success: int, final_failed: int
    ):
        """Print final statistics."""
        total_success = initial_success + retry_success

        with self.stats_lock:
            ti = self.total_input_tokens
            to = self.total_output_tokens

        self.logger.info("=" * 80)
        self.logger.info("Translation Statistics:")
        self.logger.info(f" Total items: {total}")
        self.logger.info(f" Initial success: {initial_success}")
        self.logger.info(f" Retry success: {retry_success}")
        self.logger.info(f" Total success: {total_success}")
        self.logger.info(f" Final failed: {final_failed}")
        self.logger.info(f" Success rate: {total_success/total*100:.1f}%")
        self.logger.info(f" Token usage: input {ti}, output {to}")
        self.logger.info(f" Workers: {self.settings.worker_count}")
        self.logger.info("=" * 80)


def main():
    """Main entry point."""
    # Load environment variables from .env file
    env_path = Path(__file__).parent / ".env"
    load_dotenv(dotenv_path=env_path)

    # Get configuration from environment
    groq_api_key = os.getenv("GROQ_API_KEY")
    lang_codes_str = os.getenv("LANG_CODES", "en,de")
    srt_dir = os.getenv("SRT_DIR", r"C:\langgraph_translater\a_channel\b_content")

    # Optional settings with defaults
    model_priority_index = int(os.getenv("MODEL_PRIORITY_INDEX", "0"))
    worker_count = int(
        os.getenv("WORKER_COUNT", str(DefaultSettings.DEFAULT_WORKER_COUNT))
    )
    batch_size = int(os.getenv("BATCH_SIZE", str(DefaultSettings.DEFAULT_BATCH_SIZE)))
    save_interval = int(
        os.getenv("SAVE_INTERVAL", str(DefaultSettings.DEFAULT_SAVE_INTERVAL))
    )

    # Validate required settings
    if not groq_api_key:
        print("Error: GROQ_API_KEY not found in environment variables")
        print("Please create a .env file with your GROQ_API_KEY")
        sys.exit(1)

    # Create settings
    try:
        settings = SettingsManager(
            groq_api_key=groq_api_key,
            lang_codes_str=lang_codes_str,
            srt_dir=srt_dir,
            model_priority_index=model_priority_index,
            worker_count=worker_count,
            batch_size=batch_size,
            save_interval=save_interval,
        )
    except ValueError as e:
        print(f"Configuration error: {e}")
        sys.exit(1)

    # Create orchestrator
    orchestrator = TranslationOrchestrator(settings)

    # Run translation
    orchestrator.run_batch_translation()

    print("\nTranslation completed!")


if __name__ == "__main__":
    main()
