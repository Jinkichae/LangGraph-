"""Example tests for the translation system."""

import unittest
import sys
import os

# Add parent directory to path
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, parent_dir)

# Now import modules
import config.settings
import config.constants
import core.translation_request
import builders.pipeline_builder

SettingsManager = config.settings.SettingsManager
DefaultSettings = config.settings.DefaultSettings
AppConstants = config.constants.AppConstants
TranslationRequest = core.translation_request.TranslationRequest
TranslationPipelineBuilder = builders.pipeline_builder.TranslationPipelineBuilder


class TestTranslationRequest(unittest.TestCase):
    """Test TranslationRequest data object."""

    def test_valid_request(self):
        """Test valid translation request."""
        request = TranslationRequest(
            index=1,
            ko_text="안녕하세요",
            context="컨텍스트",
            target_langs=["en", "ja"]
        )
        self.assertTrue(request.is_valid())
        self.assertEqual(request.index, 1)
        self.assertEqual(request.ko_text, "안녕하세요")
        self.assertFalse(request.success)

    def test_invalid_empty_text(self):
        """Test request with empty text."""
        request = TranslationRequest(
            index=1,
            ko_text="",
            context="",
            target_langs=["en"]
        )
        self.assertFalse(request.is_valid())

    def test_invalid_empty_langs(self):
        """Test request with no target languages."""
        request = TranslationRequest(
            index=1,
            ko_text="안녕하세요",
            context="",
            target_langs=[]
        )
        self.assertFalse(request.is_valid())

    def test_mark_success(self):
        """Test marking request as successful."""
        request = TranslationRequest(
            index=1,
            ko_text="안녕하세요",
            context="",
            target_langs=["en"]
        )
        translations = {"en": "Hello"}
        request.mark_success(translations)

        self.assertTrue(request.success)
        self.assertEqual(request.translations, translations)
        self.assertIsNone(request.error)

    def test_mark_failure(self):
        """Test marking request as failed."""
        request = TranslationRequest(
            index=1,
            ko_text="안녕하세요",
            context="",
            target_langs=["en"]
        )
        error_msg = "API Error"
        request.mark_failure(error_msg)

        self.assertFalse(request.success)
        self.assertEqual(request.error, error_msg)

    def test_increment_attempt(self):
        """Test attempt counter."""
        request = TranslationRequest(
            index=1,
            ko_text="안녕하세요",
            context="",
            target_langs=["en"]
        )
        self.assertEqual(request.attempt_count, 0)

        request.increment_attempt()
        self.assertEqual(request.attempt_count, 1)

        request.increment_attempt()
        self.assertEqual(request.attempt_count, 2)


class TestSettingsManager(unittest.TestCase):
    """Test SettingsManager."""

    def test_valid_settings(self):
        """Test creating valid settings."""
        settings = SettingsManager(
            groq_api_key="test_key",
            lang_codes_str="en,de,ja",
            srt_dir="/path/to/srt"
        )
        self.assertEqual(settings.groq_api_key, "test_key")
        self.assertEqual(settings.lang_codes_list, ["en", "de", "ja"])
        self.assertEqual(settings.srt_dir, "/path/to/srt")

    def test_invalid_empty_api_key(self):
        """Test settings with empty API key."""
        with self.assertRaises(ValueError):
            SettingsManager(
                groq_api_key="",
                lang_codes_str="en",
                srt_dir="/path"
            )

    def test_invalid_empty_lang_codes(self):
        """Test settings with empty language codes."""
        with self.assertRaises(ValueError):
            SettingsManager(
                groq_api_key="test_key",
                lang_codes_str="",
                srt_dir="/path"
            )

    def test_default_values(self):
        """Test default settings values."""
        settings = SettingsManager(
            groq_api_key="test_key",
            lang_codes_str="en",
            srt_dir="/path"
        )
        self.assertEqual(settings.temperature, DefaultSettings.DEFAULT_TEMPERATURE)
        self.assertEqual(settings.max_retries, DefaultSettings.DEFAULT_MAX_RETRIES)
        self.assertEqual(settings.worker_count, DefaultSettings.DEFAULT_WORKER_COUNT)


class TestAppConstants(unittest.TestCase):
    """Test AppConstants."""

    def test_constants_exist(self):
        """Test that required constants exist."""
        self.assertIsNotNone(AppConstants.INDEX_FILENAME)
        self.assertIsNotNone(AppConstants.JSON_FILENAME)
        self.assertIsNotNone(AppConstants.SOURCE_SUBTITLE_FILENAME)
        self.assertIsInstance(AppConstants.MODEL_PRIORITY_LIST, list)
        self.assertGreater(len(AppConstants.MODEL_PRIORITY_LIST), 0)

    def test_system_message(self):
        """Test system message exists and is not empty."""
        self.assertIsNotNone(AppConstants.SYSTEM_MESSAGE)
        self.assertGreater(len(AppConstants.SYSTEM_MESSAGE), 0)


class TestPipelineBuilder(unittest.TestCase):
    """Test TranslationPipelineBuilder."""

    def test_empty_pipeline_raises_error(self):
        """Test that building empty pipeline raises error."""
        builder = TranslationPipelineBuilder()
        with self.assertRaises(ValueError):
            builder.build()

    def test_pipeline_with_validation(self):
        """Test pipeline with validation handler."""
        builder = TranslationPipelineBuilder()
        pipeline = builder.add_validation().build()
        self.assertIsNotNone(pipeline)

    def test_pipeline_reset(self):
        """Test resetting pipeline builder."""
        builder = TranslationPipelineBuilder()
        builder.add_validation()
        builder.reset()

        with self.assertRaises(ValueError):
            builder.build()


def run_tests():
    """Run all tests."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
