import json
from datetime import datetime

def format_log(level, message, details=None, extra=None):  # extra parametresini ekledik
    """
    Formats a log entry as a JSON string.

    Args:
        level (str): The severity level of the log (e.g., DEBUG, INFO, WARNING, ERROR, CRITICAL).
        message (str): The main log message.
        details (dict, optional): Additional context or details for the log message.
        extra (dict, optional): Extra key-value pairs to include in the log entry.

    Returns:
        str: A JSON string representing the formatted log entry.
    """
    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "level": level,
        "message": message,
        "details": details if details else {},
    }
    if extra:
        log_entry.update(extra)  # extra parametresindeki değerleri log kaydına ekliyoruz
    return json.dumps(log_entry)

# Example Usage
if __name__ == "__main__":
    # Example of a formatted log entry
    print(format_log("INFO", "Application started", {"module": "main", "function": "startup"}))
