"""File utilities following DRY principle."""

import os
import json
from typing import Any, Dict, List, Optional

from config.constants import AppConstants


class FileUtils:
    """Common file operations."""

    @staticmethod
    def read_with_fallback_encoding(file_path: str) -> str:
        """
        Read file with fallback encoding options.

        Args:
            file_path: Path to file

        Returns:
            File content as string

        Raises:
            IOError: If file cannot be read with any encoding
        """
        for encoding in AppConstants.ENCODING_OPTIONS:
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    return f.read()
            except (UnicodeDecodeError, LookupError):
                continue

        raise IOError(f"Cannot read file {file_path} with any supported encoding")

    @staticmethod
    def read_json_file(file_path: str, default: Any = None) -> Any:
        """
        Read JSON file with error handling.

        Args:
            file_path: Path to JSON file
            default: Default value if file doesn't exist or is invalid

        Returns:
            Parsed JSON data or default value
        """
        if not os.path.exists(file_path):
            return default

        try:
            content = FileUtils.read_with_fallback_encoding(file_path)
            if not content.strip():
                return default
            return json.loads(content)
        except (json.JSONDecodeError, IOError):
            return default

    @staticmethod
    def write_json_file(file_path: str, data: Any, indent: int = 4):
        """
        Write data to JSON file.

        Args:
            file_path: Path to JSON file
            data: Data to write
            indent: JSON indentation level
        """
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)

    @staticmethod
    def append_to_json_list(file_path: str, new_item: Dict[str, Any]):
        """
        Append item to JSON file containing a list.

        Args:
            file_path: Path to JSON file
            new_item: Item to append
        """
        data_list = FileUtils.read_json_file(file_path, default=[])

        if not isinstance(data_list, list):
            data_list = []

        data_list.append(new_item)
        FileUtils.write_json_file(file_path, data_list)

    @staticmethod
    def ensure_directory_exists(directory: str):
        """
        Ensure directory exists, create if it doesn't.

        Args:
            directory: Directory path
        """
        os.makedirs(directory, exist_ok=True)
