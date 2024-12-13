import ipaddress
import yaml
from utils.config_manager import load_config
from logB.logger import Logger
from utils.display import Display


class TaskGenerator:
    """
    A utility class for generating task lists from IP/CIDR blocks and blacklist configurations.
    """

    def __init__(self):
        # Initialize logger and display
        config = load_config()
        self.logger = Logger(log_file_path=config['logging']['app_log_path'])
        self.error_logger = Logger(log_file_path=config['logging']['error_log_path'])
        self.display = Display()

    def parse_ip_list(self, file_path):
        """
        Parses a YAML file containing CIDR blocks and converts them to /32 IPs.

        Args:
            file_path (str): Path to the YAML file.

        Returns:
            list: A list of /32 IP addresses.
        """
        try:
            with open(file_path, "r") as f:
                cidr_blocks = yaml.safe_load(f)

            ip_list = []
            for cidr in cidr_blocks:
                try:
                    network = ipaddress.ip_network(cidr, strict=False)
                    ip_list.extend([str(ip) for ip in network.hosts()])
                except ValueError as e:
                    error_message = f"Invalid CIDR block {cidr}: {e}"
                    self.error_logger.error(error_message, extra={"function": "parse_ip_list", "file": "task_generator.py", "cidr": cidr})
                    self.display.print_error(f"\u274c {error_message}")
            self.logger.info(f"Parsed {len(ip_list)} IPs from {file_path}")
            return ip_list

        except FileNotFoundError as e:
            error_message = f"File not found: {file_path}"
            self.error_logger.error(error_message, extra={"function": "parse_ip_list", "file": "task_generator.py"})
            self.display.print_error(f"\u274c {error_message}")
            return []
        except Exception as e:
            error_message = f"Error parsing IP list: {e}"
            self.error_logger.error(error_message, extra={"function": "parse_ip_list", "file": "task_generator.py"})
            self.display.print_error(f"\u274c {error_message}")
            return []

    def get_blacklist_config(self):
        """
        Retrieves the blacklist configuration using the config_manager.

        Returns:
            list: A list of blacklist configurations.
        """
        try:
            config = load_config()
            if "blacklists" not in config:
                raise KeyError("Blacklist configuration is missing in the config file.")
            self.logger.info("Blacklist configuration loaded successfully.")
            return config["blacklists"]
        except KeyError as e:
            error_message = f"KeyError: {e}"
            self.error_logger.error(error_message, extra={"function": "get_blacklist_config", "file": "task_generator.py"})
            self.display.print_error(f"\u274c {error_message}")
            return []
        except Exception as e:
            error_message = f"Error retrieving blacklist configuration: {e}"
            self.error_logger.error(error_message, extra={"function": "get_blacklist_config", "file": "task_generator.py"})
            self.display.print_error(f"\u274c {error_message}")
            return []

    def generate_task_list(self, ip_list, blacklist_list):
        """
        Generates all possible tasks for given IPs and blacklists.

        Args:
            ip_list (list): List of /32 IP addresses.
            blacklist_list (list): List of blacklist configurations.

        Returns:
            list: A list of dictionaries representing tasks.
        """
        try:
            task_list = []
            for ip in ip_list:
                for blacklist in blacklist_list:
                    task_list.append({
                        "ip": ip,
                        "blacklist_name": blacklist["name"],
                        "dns": blacklist["dns"],
                        "removal_link": blacklist["removal_link"],
                        "removal_method": blacklist["removal_method"]
                    })
            self.logger.info(f"Generated {len(task_list)} tasks.")
            self.display.print_success(f"\u2714\ufe0f Generated {len(task_list)} tasks.")
            return task_list

        except Exception as e:
            error_message = f"Error generating task list: {e}"
            self.error_logger.error(error_message, extra={"function": "generate_task_list", "file": "task_generator.py"})
            self.display.print_error(f"\u274c {error_message}")
            return []
