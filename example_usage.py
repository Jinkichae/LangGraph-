"""
Example usage scenarios for the LangGraph Subtitle Translator.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

from config.settings import SettingsManager
from main import TranslationOrchestrator


def example_basic_usage():
    """Example 1: Basic usage with environment variables."""
    print("=" * 80)
    print("Example 1: Basic Usage")
    print("=" * 80)

    # Load environment variables
    env_path = Path(__file__).parent / ".env"
    load_dotenv(dotenv_path=env_path)

    # Create settings from environment
    settings = SettingsManager(
        groq_api_key=os.getenv("GROQ_API_KEY"),
        lang_codes_str=os.getenv("LANG_CODES", "en,de"),
        srt_dir=os.getenv("SRT_DIR"),
    )

    # Create orchestrator
    orchestrator = TranslationOrchestrator(settings)

    # Run translation
    orchestrator.run_batch_translation()

    print("\nTranslation completed!")


def example_custom_settings():
    """Example 2: Custom settings without environment variables."""
    print("=" * 80)
    print("Example 2: Custom Settings")
    print("=" * 80)

    # Create settings programmatically
    settings = SettingsManager(
        groq_api_key="your_api_key_here",
        lang_codes_str="en,de,ja,es,fr",
        srt_dir=r"C:\path\to\subtitles",
        model_priority_index=3,  # Use llama-3.3-70b-versatile
        temperature=0.2,
        max_retries=5,
        worker_count=8,
        batch_size=16,
        save_interval=20,
    )

    print(f"Settings: {settings}")

    # Create orchestrator
    orchestrator = TranslationOrchestrator(settings)

    # Run with custom parameters
    orchestrator.run_batch_translation(
        start_index=1,
        worker_count=8,
        batch_size=16,
        save_interval=20,
    )

    print("\nTranslation completed!")


def example_resume_translation():
    """Example 3: Resume interrupted translation."""
    print("=" * 80)
    print("Example 3: Resume Translation")
    print("=" * 80)

    # Load settings
    settings = SettingsManager(
        groq_api_key=os.getenv("GROQ_API_KEY"),
        lang_codes_str="en,de,ja",
        srt_dir=r"C:\path\to\subtitles",
    )

    # Create orchestrator
    orchestrator = TranslationOrchestrator(settings)

    # Progress is automatically loaded from index file
    print("Resuming from last saved position...")

    orchestrator.run_batch_translation()

    print("\nTranslation completed!")


def example_manual_retry():
    """Example 4: Manually retry failed items."""
    print("=" * 80)
    print("Example 4: Manual Retry")
    print("=" * 80)

    # Load settings
    settings = SettingsManager(
        groq_api_key=os.getenv("GROQ_API_KEY"),
        lang_codes_str="en,de",
        srt_dir=r"C:\path\to\subtitles",
    )

    # Create orchestrator
    orchestrator = TranslationOrchestrator(settings)

    # Retry all failed items (finds them automatically)
    print("Searching for failed items...")
    orchestrator.manual_retry_failed(max_retries=3)

    print("\nRetry completed!")


def example_custom_pipeline():
    """Example 5: Build custom translation pipeline."""
    print("=" * 80)
    print("Example 5: Custom Pipeline")
    print("=" * 80)

    from builders.pipeline_builder import TranslationPipelineBuilder
    from core.translation_executor import TranslationExecutor
    from core.subtitle_manager import SubtitleManager
    from utils.path_manager import PathManager
    from utils.logger_utils import LoggerUtils

    # Setup
    settings = SettingsManager(
        groq_api_key=os.getenv("GROQ_API_KEY"),
        lang_codes_str="en,de",
        srt_dir=r"C:\path\to\subtitles",
    )

    logger = LoggerUtils.setup_logger("CustomPipeline")
    path_manager = PathManager(settings.srt_dir)
    subtitle_manager = SubtitleManager(path_manager, settings.lang_codes_list, logger)
    executor = TranslationExecutor(settings, "llama-3.3-70b-versatile", logger)

    # Build custom pipeline (skip persistence for dry run)
    pipeline = (
        TranslationPipelineBuilder()
        .add_validation()
        .add_execution(executor, max_attempts=2)
        .add_logging(logger)  # No persistence
        .build()
    )

    # Use pipeline
    from core.translation_request import TranslationRequest

    request = TranslationRequest(
        index=1,
        ko_text="안녕하세요",
        context="이전 문맥",
        target_langs=["en", "de"],
    )

    result = pipeline.handle(request)

    print(f"Success: {result.success}")
    print(f"Translations: {result.translations}")


def example_batch_processing():
    """Example 6: Process specific batch of subtitles."""
    print("=" * 80)
    print("Example 6: Batch Processing")
    print("=" * 80)

    settings = SettingsManager(
        groq_api_key=os.getenv("GROQ_API_KEY"),
        lang_codes_str="en,de,ja",
        srt_dir=r"C:\path\to\subtitles",
    )

    orchestrator = TranslationOrchestrator(settings)

    # Process subtitles 100-200 with aggressive settings
    orchestrator.run_batch_translation(
        start_index=100,  # Start from index 100
        worker_count=10,  # More workers
        batch_size=20,    # Larger batches
        save_interval=50, # Save less frequently
    )

    print("\nBatch processing completed!")


def example_different_models():
    """Example 7: Try different models."""
    print("=" * 80)
    print("Example 7: Different Models")
    print("=" * 80)

    from config.constants import AppConstants

    # List available models
    print("Available models:")
    for i, model in enumerate(AppConstants.MODEL_PRIORITY_LIST):
        print(f"  {i}: {model}")

    # Try with different model
    settings = SettingsManager(
        groq_api_key=os.getenv("GROQ_API_KEY"),
        lang_codes_str="en",
        srt_dir=r"C:\path\to\subtitles",
        model_priority_index=6,  # openai/gpt-oss-120b
    )

    orchestrator = TranslationOrchestrator(settings)

    print(f"\nUsing model: {orchestrator.model_name}")

    orchestrator.run_batch_translation()


def print_menu():
    """Print example menu."""
    print("\n" + "=" * 80)
    print("LangGraph Subtitle Translator - Example Usage")
    print("=" * 80)
    print("1. Basic Usage")
    print("2. Custom Settings")
    print("3. Resume Translation")
    print("4. Manual Retry Failed Items")
    print("5. Custom Pipeline")
    print("6. Batch Processing")
    print("7. Different Models")
    print("0. Exit")
    print("=" * 80)


if __name__ == "__main__":
    # Load environment for examples
    load_dotenv()

    while True:
        print_menu()
        choice = input("\nSelect example (0-7): ").strip()

        if choice == "0":
            print("Exiting...")
            break
        elif choice == "1":
            example_basic_usage()
        elif choice == "2":
            example_custom_settings()
        elif choice == "3":
            example_resume_translation()
        elif choice == "4":
            example_manual_retry()
        elif choice == "5":
            example_custom_pipeline()
        elif choice == "6":
            example_batch_processing()
        elif choice == "7":
            example_different_models()
        else:
            print("Invalid choice. Please try again.")

        input("\nPress Enter to continue...")
