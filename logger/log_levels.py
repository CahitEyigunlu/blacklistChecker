"""
Defines the log levels used in the logging system.
Each level represents a different severity or type of log message.
"""

# Debug level: used for detailed diagnostic information, primarily useful for developers.
DEBUG = "DEBUG"

# Info level: used for informational messages that highlight the progress of the application.
INFO = "INFO"

# Warning level: used for potentially harmful situations that indicate a possible issue.
WARNING = "WARNING"

# Error level: used when an error occurs that might allow the application to continue running.
ERROR = "ERROR"

# Critical level: used for severe errors that may cause the application to abort.
CRITICAL = "CRITICAL"

# Log level order for easy comparison, if needed in filtering or threshold-based logging.
LEVELS = [DEBUG, INFO, WARNING, ERROR, CRITICAL]
