"""
Application constants following SSOT (Single Source of Truth) principle.
All constants are centralized here for easy maintenance.
"""


class AppConstants:
    """Central repository for all application constants."""

    # File names
    INDEX_FILENAME = "37_langgraph_translate_all_language_with_context.txt"
    JSON_FILENAME = "37_langgraph_translate_all_language_with_context.json"
    SOURCE_SUBTITLE_FILENAME = "100_translate.srt"

    # Model priorities
    MODEL_PRIORITY_LIST = [
        "openai/gpt-oss-20b",
        "qwen/qwen3-32b",
        "gemma2-9b-it",
        "llama-3.3-70b-versatile",
        "meta-llama/llama-4-maverick-17b-128e-instruct",
        "moonshotai/kimi-k2-instruct",
        "openai/gpt-oss-120b",
        "deepseek-r1-distill-llama-70b",
    ]

    # Encoding options
    ENCODING_OPTIONS = ["utf-8", "cp949", "euc-kr"]

    # Response validation patterns
    REPETITIVE_PATTERNS = [
        "a proper translation would be",
        "should be a statement matching",
        "is not appropriate",
        "let me check",
        "i need to",
        "looking at the",
    ]

    TOOL_PATTERNS = [
        "calling tool",
        "using tool",
        "tool call",
        "invoke",
        "executing",
    ]

    # Translation system messages
    SYSTEM_MESSAGE = """당신은 다국어 단문 번역 전문가입니다.
지침:
1. 모든 언어로 정확하고 자연스럽게 번역하세요.
2. 번역 후 update_translations_in_memory 도구를 정확히 1회 호출.
3. 도구 호출 시 반드시 {"translations": {"ko": "...", "en": "...", ...}} 형식 준수.
4. 호출 후 '번역 완료'라고 응답 및 종료.
5. 추가 분석, 재호출 금지.

품질:
- 문맥 반영 자연스러움
- 문법, 의미 정확
- 원문의 뉘앙스 유지
"""

    USER_REQUEST_TEMPLATE = """다음 한글 텍스트를 다음 언어({target_langs})로 자연스럽고 세련되게 번역하세요.
1. 문맥을 고려해 의도와 뉘앙스를 세련되게 표현하세요.
2. 의미를 정확히 전달하고 문법적으로 올바른 번역이어야 합니다.
3. ko는 원문 그대로; 문맥만 참고하세요.

문맥: {context}

번역할 텍스트: {text}"""

    # Logging format
    LOG_FORMAT = "[%(asctime)s] [%(levelname)s] [Thread-%(thread)d] %(message)s"
    LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
