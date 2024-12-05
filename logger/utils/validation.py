# validation.py

from datetime import datetime
import json

def validate_log_entry(entry):
    """
    Validates a log entry to ensure it conforms to the required format.

    Args:
        entry (dict): The log entry to validate, expected to be in dictionary format.

    Returns:
        bool: True if the log entry is valid, False otherwise.
    """
    required_keys = ["timestamp", "level", "message"]

    # Check if all required keys are present
    for key in required_keys:
        if key not in entry:
            print(f"Validation failed: Missing key '{key}' in log entry.")
            return False

    # Validate timestamp format (ISO 8601)
    try:
        datetime.fromisoformat(entry["timestamp"].replace("Z", "+00:00"))
    except ValueError:
        print("Validation failed: Invalid timestamp format.")
        return False

    # Validate level
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if entry["level"] not in valid_levels:
        print(f"Validation failed: Invalid log level '{entry['level']}'.")
        return False

    # Ensure message is a non-empty string
    if not isinstance(entry["message"], str) or not entry["message"]:
        print("Validation failed: 'message' should be a non-empty string.")
        return False

    return True

def is_json_serializable(data):
    """
    Checks if the provided data is JSON serializable.

    Args:
        data (any): The data to check for JSON serializability.

    Returns:
        bool: True if the data is JSON serializable, False otherwise.
    """
    try:
        json.dumps(data)
        return True
    except (TypeError, OverflowError):
        print("Validation failed: Data is not JSON serializable.")
        return False

def validate_log_size(log_path, max_size_mb=10):
    """
    Validates the size of the log file to ensure it does not exceed a maximum limit.

    Args:
        log_path (str): The path to the log file.
        max_size_mb (int): The maximum file size in megabytes (default is 10 MB).

    Returns:
        bool: True if the log file size is within the limit, False if it exceeds.
    """
    max_size_bytes = max_size_mb * 1024 * 1024
    try:
        file_size = os.path.getsize(log_path)
        if file_size > max_size_bytes:
            print(f"Validation failed: Log file size exceeds {max_size_mb} MB.")
            return False
        return True
    except FileNotFoundError:
        print("Validation failed: Log file not found.")
        return False
