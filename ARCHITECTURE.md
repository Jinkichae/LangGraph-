# Architecture Documentation

## Design Patterns

### 1. Builder Pattern

The **TranslationPipelineBuilder** implements the Builder pattern to construct translation processing pipelines with a fluent interface.

```python
pipeline = (TranslationPipelineBuilder()
    .add_validation()
    .add_execution(executor, max_attempts=3)
    .add_persistence(subtitle_manager)
    .add_logging(logger)
    .build())
```

**Benefits:**
- Flexible pipeline configuration
- Readable, declarative syntax
- Easy to add/remove processing steps
- Separates construction from representation

### 2. Chain of Responsibility Pattern

Handlers process translation requests sequentially, each with a specific responsibility:

```
Request → ValidationHandler → ExecutionHandler → PersistenceHandler → LoggingHandler
```

**Handler Responsibilities:**

1. **ValidationHandler**: Validates request data
2. **ExecutionHandler**: Executes translation with retry logic
3. **PersistenceHandler**: Saves results to subtitle files
4. **LoggingHandler**: Logs outcomes

**Benefits:**
- Decoupled request processing
- Easy to add/modify/remove steps
- Each handler has single responsibility
- Flexible request routing

## SOLID Principles

### Single Responsibility Principle (SRP)

Each class has one reason to change:

- `SubtitleManager`: Manages subtitle files only
- `TranslationExecutor`: Executes translations only
- `PathManager`: Manages file paths only
- `FileUtils`: Handles file operations only
- `LoggerUtils`: Configures loggers only

### Open-Closed Principle (OCP)

- Open for extension: Add new handlers to pipeline
- Closed for modification: Core handlers don't change

```python
# Easy to add new handler
class CustomHandler(TranslationHandler):
    def handle(self, request):
        # Custom logic
        return self._call_next(request)

# Add to pipeline without modifying existing code
pipeline = builder.add_custom(CustomHandler()).build()
```

### Liskov Substitution Principle (LSP)

All handlers inherit from `TranslationHandler` and can be substituted:

```python
def process_with_handler(handler: TranslationHandler, request: TranslationRequest):
    return handler.handle(request)

# Works with any handler
process_with_handler(ValidationHandler(), request)
process_with_handler(ExecutionHandler(executor), request)
```

### Interface Segregation Principle (ISP)

Clients depend only on interfaces they use:

- Handlers only implement `handle()` method
- Executors only implement translation execution
- Managers only implement their specific operations

### Dependency Inversion Principle (DIP)

High-level modules depend on abstractions:

```python
class ExecutionHandler(TranslationHandler):
    def __init__(self, executor: TranslationExecutor):
        # Depends on executor abstraction, not concrete implementation
        self.executor = executor
```

## DRY (Don't Repeat Yourself)

### Centralized File Operations

All file operations through `FileUtils`:

```python
# Before (repeated code)
with open(file1, 'r', encoding='utf-8') as f:
    content1 = f.read()

with open(file2, 'r', encoding='utf-8') as f:
    content2 = f.read()

# After (DRY)
content1 = FileUtils.read_with_fallback_encoding(file1)
content2 = FileUtils.read_with_fallback_encoding(file2)
```

### Centralized Path Management

All paths through `PathManager`:

```python
# Before (scattered path logic)
source_path = os.path.join(base_dir, "100_translate.srt")
en_path = os.path.join(base_dir, "en.srt")
de_path = os.path.join(base_dir, "de.srt")

# After (centralized)
source_path = path_manager.get_source_subtitle_path()
en_path = path_manager.get_language_subtitle_path("en")
de_path = path_manager.get_language_subtitle_path("de")
```

### Centralized Logger Configuration

All loggers through `LoggerUtils`:

```python
# Before (repeated logger setup)
logger = logging.getLogger("MyLogger")
handler = logging.StreamHandler()
formatter = logging.Formatter("[%(asctime)s] %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

# After (DRY)
logger = LoggerUtils.setup_logger("MyLogger")
```

## SSOT (Single Source of Truth)

### AppConstants

All application constants in one place:

```python
class AppConstants:
    INDEX_FILENAME = "37_langgraph_translate_all_language_with_context.txt"
    JSON_FILENAME = "37_langgraph_translate_all_language_with_context.json"
    SOURCE_SUBTITLE_FILENAME = "100_translate.srt"
    MODEL_PRIORITY_LIST = [...]
    SYSTEM_MESSAGE = "..."
    # ... all constants here
```

**Benefits:**
- Change constant once, effect everywhere
- No magic strings scattered in code
- Easy to maintain and update
- Clear documentation of all values

### DefaultSettings

All default values in one place:

```python
class DefaultSettings:
    DEFAULT_TEMPERATURE = 0.1
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_WORKER_COUNT = 6
    # ... all defaults here
```

## Component Interaction

```
┌─────────────────┐
│  main.py        │
│ (Orchestrator)  │
└────────┬────────┘
         │
         ├──> SettingsManager (config)
         │
         ├──> PathManager (utils)
         │
         ├──> SubtitleManager (core)
         │
         ├──> TranslationExecutor (core)
         │
         └──> PipelineBuilder (builders)
              │
              ├──> ValidationHandler
              ├──> ExecutionHandler
              ├──> PersistenceHandler
              └──> LoggingHandler
```

## Data Flow

```
1. Load Settings
   └─> SettingsManager validates configuration

2. Initialize Components
   ├─> PathManager (file paths)
   ├─> SubtitleManager (loads subtitles)
   └─> TranslationExecutor (LLM setup)

3. Build Pipeline
   └─> TranslationPipelineBuilder chains handlers

4. Process Requests
   ├─> Create TranslationRequest
   ├─> Pass through pipeline
   │   ├─> Validation
   │   ├─> Execution (with retry)
   │   ├─> Persistence
   │   └─> Logging
   └─> Update statistics

5. Save Progress
   ├─> Save subtitle files
   └─> Save progress/stats
```

## Extension Points

### Add New Handler

```python
class MetricsHandler(TranslationHandler):
    """Collect translation metrics."""

    def handle(self, request: TranslationRequest):
        # Collect metrics
        self.metrics.record(request)
        return self._call_next(request)

# Add to pipeline
pipeline = (builder
    .add_validation()
    .add_execution(executor)
    .add_custom(MetricsHandler())  # New handler
    .add_persistence(subtitle_manager)
    .build())
```

### Add New Model

```python
# In config/constants.py
MODEL_PRIORITY_LIST = [
    # ... existing models ...
    "new-model-name",  # Add here
]

# Use with MODEL_PRIORITY_INDEX environment variable
```

### Add New Utility

```python
# In utils/new_utility.py
class NewUtility:
    @staticmethod
    def new_function():
        # Implementation
        pass

# Export in utils/__init__.py
from .new_utility import NewUtility
__all__ = [..., "NewUtility"]
```

## Testing Strategy

### Unit Tests

Test individual components in isolation:

```python
def test_translation_request_validation():
    request = TranslationRequest(
        index=1,
        ko_text="",
        context="",
        target_langs=["en"]
    )
    assert not request.is_valid()
```

### Integration Tests

Test component interactions:

```python
def test_pipeline_execution():
    pipeline = (builder
        .add_validation()
        .add_execution(mock_executor)
        .build())

    request = create_test_request()
    result = pipeline.handle(request)

    assert result.success
```

### End-to-End Tests

Test complete workflows:

```python
def test_full_translation_workflow():
    orchestrator = TranslationOrchestrator(test_settings)
    orchestrator.run_batch_translation()

    # Verify all files created
    assert all_subtitle_files_exist()
```

## Performance Considerations

### Thread Pool

- Concurrent translation with `ThreadPoolExecutor`
- Configurable worker count
- Batch processing to avoid overwhelming API

### Memory Management

- Periodic saves to avoid memory buildup
- Lock-based synchronization for thread safety
- Efficient event loop cleanup

### Error Recovery

- Automatic retry with exponential backoff
- Failed item tracking and re-processing
- Progress saving for resume capability

## Security Considerations

### API Key Management

- Load from environment variables (`.env`)
- Never commit API keys to repository
- Use `.env.example` template for documentation

### Input Validation

- Validate all user inputs in `SettingsManager`
- Validate request data in `ValidationHandler`
- Sanitize file paths through `PathManager`

### Error Handling

- Graceful degradation on errors
- Detailed error logging
- No sensitive data in logs
