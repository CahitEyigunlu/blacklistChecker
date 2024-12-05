# access_control.py

from datetime import datetime
import json
import os

# Access control settings
ACCESS_LOG_FILE = os.path.join(os.getcwd(), "logs", "access_logs.json")

# Ensure the access log file exists
os.makedirs(os.path.dirname(ACCESS_LOG_FILE), exist_ok=True)
if not os.path.exists(ACCESS_LOG_FILE):
    with open(ACCESS_LOG_FILE, 'w') as f:
        json.dump([], f)

# Role-based access control (RBAC) settings
ROLE_PERMISSIONS = {
    "admin": ["read", "write", "delete"],
    "auditor": ["read"],
    "user": []  # Basic users have no access to logs
}

def check_access(user_role, required_permission):
    """
    Checks if a user role has the required permission.
    
    Args:
        user_role (str): The role of the user (e.g., 'admin', 'auditor').
        required_permission (str): The permission required (e.g., 'read', 'write', 'delete').
    
    Returns:
        bool: True if the user has the required permission, False otherwise.
    """
    permissions = ROLE_PERMISSIONS.get(user_role, [])
    return required_permission in permissions

def log_access(user_id, action, resource="log file"):
    """
    Logs the access attempt to the access log file, recording user details and actions.

    Args:
        user_id (str): The ID of the user attempting access.
        action (str): The action the user attempted (e.g., 'read', 'write', 'delete').
        resource (str): The resource being accessed (default: "log file").
    """
    access_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "user_id": user_id,
        "action": action,
        "resource": resource
    }
    # Append the access entry to the access log file
    with open(ACCESS_LOG_FILE, 'r+') as f:
        access_log = json.load(f)
        access_log.append(access_entry)
        f.seek(0)
        json.dump(access_log, f, indent=4)

def request_access(user_id, user_role, action):
    """
    Handles an access request by checking permissions and logging the attempt.
    
    Args:
        user_id (str): The ID of the user requesting access.
        user_role (str): The role of the user (e.g., 'admin', 'auditor').
        action (str): The action the user is trying to perform (e.g., 'read', 'write', 'delete').

    Returns:
        str: "Access granted" if permission is granted, "Access denied" otherwise.
    """
    if check_access(user_role, action):
        log_access(user_id, action)
        return "Access granted."
    else:
        log_access(user_id, f"attempted {action} - denied")
        return "Access denied."

# Example usage
if __name__ == "__main__":
    # Test cases
    user_id = "user_123"
    
    print(request_access(user_id, "admin", "read"))       # Expected: Access granted
    print(request_access(user_id, "auditor", "write"))    # Expected: Access denied
    print(request_access(user_id, "user", "read"))        # Expected: Access denied
    print(request_access(user_id, "admin", "delete"))     # Expected: Access granted
