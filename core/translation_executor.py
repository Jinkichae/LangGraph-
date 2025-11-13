"""Translation executor using LangChain and LangGraph."""

import asyncio
import logging
from typing import Dict, Tuple, Optional, List

from langchain_groq import ChatGroq
from langchain.tools import StructuredTool
from langgraph.prebuilt import create_react_agent

from config.constants import AppConstants
from config.settings import SettingsManager


class TranslationExecutor:
    """
    Executes translation using LangChain agent.
    Responsibilities:
    - Create LLM and tools
    - Execute translation
    - Validate responses
    - Track token usage
    """

    def __init__(
        self,
        settings: SettingsManager,
        model_name: str,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize translation executor.

        Args:
            settings: Settings manager
            model_name: Model name to use
            logger: Logger instance
        """
        self.settings = settings
        self.model_name = model_name
        self.logger = logger or logging.getLogger(__name__)

    def create_llm(self) -> ChatGroq:
        """
        Create a new LLM instance.

        Returns:
            ChatGroq instance
        """
        return ChatGroq(
            model=self.model_name,
            api_key=self.settings.groq_api_key,
            temperature=self.settings.temperature,
        )

    def create_dummy_tool(self) -> StructuredTool:
        """
        Create a dummy tool for capturing translations.

        Returns:
            StructuredTool instance
        """

        def dummy_func(translations: Dict[str, str]):
            return {"result": "success", "data": translations}

        return StructuredTool.from_function(
            func=dummy_func,
            name="update_translations_in_memory",
            description="각 언어별 번역 결과를 저장합니다",
            return_direct=True,
        )

    def build_messages(
        self, ko_text: str, context: str, target_langs: List[str]
    ) -> list:
        """
        Build messages for the agent.

        Args:
            ko_text: Korean text to translate
            context: Context for translation
            target_langs: Target language codes

        Returns:
            List of messages
        """
        user_request = AppConstants.USER_REQUEST_TEMPLATE.format(
            target_langs=",".join(target_langs), context=context, text=ko_text
        )

        return [
            {"role": "system", "content": AppConstants.SYSTEM_MESSAGE},
            {"role": "user", "content": user_request},
        ]

    def extract_translations(self, response: dict) -> Optional[Dict[str, str]]:
        """
        Extract translations from agent response.

        Args:
            response: Agent response

        Returns:
            Dictionary of translations or None
        """
        try:
            for msg in response.get("messages", []):
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    for call in msg.tool_calls:
                        if call.get("name") == "update_translations_in_memory":
                            args = call.get("args", {})
                            if "translations" in args:
                                return args["translations"]
        except Exception as e:
            self.logger.error(f"Failed to extract translations: {e}")

        return None

    def extract_token_usage(self, response: dict) -> Tuple[int, int]:
        """
        Extract token usage from response.

        Args:
            response: Agent response

        Returns:
            Tuple of (input_tokens, output_tokens)
        """
        try:
            for msg in reversed(response.get("messages", [])):
                if hasattr(msg, "usage_metadata") and msg.usage_metadata:
                    input_t = msg.usage_metadata.get("input_tokens", 0)
                    output_t = msg.usage_metadata.get("output_tokens", 0)
                    return input_t, output_t
        except Exception as e:
            self.logger.error(f"Failed to extract token usage: {e}")

        return 0, 0

    def is_valid_response(self, response: dict) -> bool:
        """
        Validate agent response.

        Args:
            response: Agent response

        Returns:
            True if response is valid
        """
        try:
            if not response or "messages" not in response:
                return False

            last_message = response["messages"][-1]

            # Check for tool calls
            if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                return True

            # Check content
            content = last_message.content
            if not content or len(content.strip()) < 5:
                return False

            # Filter repetitive patterns
            content_lower = content.lower()
            if any(p.lower() in content_lower for p in AppConstants.REPETITIVE_PATTERNS):
                return False

            # Filter tool patterns
            if any(p.lower() in content_lower for p in AppConstants.TOOL_PATTERNS):
                return False

            return True

        except Exception as e:
            self.logger.error(f"Response validation error: {e}")
            return False

    async def execute_async(
        self, ko_text: str, context: str, target_langs: List[str]
    ) -> Tuple[bool, Dict[str, str], int, int]:
        """
        Execute translation asynchronously.

        Args:
            ko_text: Korean text to translate
            context: Context for translation
            target_langs: Target language codes

        Returns:
            Tuple of (success, translations, input_tokens, output_tokens)
        """
        try:
            # Create LLM and tools
            llm = self.create_llm()
            tools = [self.create_dummy_tool()]

            # Create agent
            agent = create_react_agent(llm, tools)

            # Build messages
            messages = self.build_messages(ko_text, context, target_langs)

            # Agent configuration
            config = {
                "recursion_limit": self.settings.get_recursion_limit(),
                "max_execution_time": self.settings.get_max_execution_time(),
                "max_iterations": self.settings.get_max_iterations(),
            }

            # Execute with timeout
            response = await asyncio.wait_for(
                agent.ainvoke({"messages": messages}, config=config),
                timeout=self.settings.get_timeout(),
            )

            # Extract token usage
            input_t, output_t = self.extract_token_usage(response)

            # Validate response
            if not self.is_valid_response(response):
                return False, {}, input_t, output_t

            # Extract translations
            translations = self.extract_translations(response)
            if not translations:
                return False, {}, input_t, output_t

            return True, translations, input_t, output_t

        except asyncio.TimeoutError:
            self.logger.error("Translation timeout")
            return False, {}, 0, 0
        except Exception as e:
            self.logger.error(f"Translation execution error: {e}")
            return False, {}, 0, 0

    def execute_sync(
        self, ko_text: str, context: str, target_langs: List[str]
    ) -> Tuple[bool, Dict[str, str], int, int]:
        """
        Execute translation synchronously (creates new event loop).

        Args:
            ko_text: Korean text to translate
            context: Context for translation
            target_langs: Target language codes

        Returns:
            Tuple of (success, translations, input_tokens, output_tokens)
        """
        loop = None
        try:
            # Create new event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # Run async function
            result = loop.run_until_complete(
                self.execute_async(ko_text, context, target_langs)
            )

            return result

        except Exception as e:
            self.logger.error(f"Sync translation error: {e}")
            return False, {}, 0, 0

        finally:
            # Clean up event loop
            if loop:
                try:
                    # Cancel pending tasks
                    pending = [task for task in asyncio.all_tasks(loop) if not task.done()]
                    for task in pending:
                        task.cancel()

                    # Wait for cancellation
                    if pending:
                        try:
                            loop.run_until_complete(
                                asyncio.wait_for(
                                    asyncio.gather(*pending, return_exceptions=True),
                                    timeout=0.5,
                                )
                            )
                        except:
                            pass

                    # Close loop
                    if not loop.is_closed():
                        loop.close()
                except:
                    pass
