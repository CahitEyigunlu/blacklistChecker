import ipaddress
import yaml
from utils.config_manager import load_config


class TaskGenerator:
    """
    A utility class for generating task lists from IP/CIDR blocks and blacklist configurations.
    """

    @staticmethod
    def parse_ip_list(file_path):
        """
        Parses a YAML file containing CIDR blocks and converts them to /32 IPs.

        Args:
            file_path (str): Path to the YAML file.

        Returns:
            list: A list of /32 IP addresses.
        """
        with open(file_path, "r") as f:
            cidr_blocks = yaml.safe_load(f)

        ip_list = []
        for cidr in cidr_blocks:
            try:
                network = ipaddress.ip_network(cidr, strict=False)
                ip_list.extend([str(ip) for ip in network.hosts()])
            except ValueError as e:
                print(f"Invalid CIDR block {cidr}: {e}")
        return ip_list

    @staticmethod
    def get_blacklist_config():
        """
        Retrieves the blacklist configuration using the config_manager.

        Returns:
            list: A list of blacklist configurations.
        """
        config = load_config()
        if "blacklists" not in config:
            raise KeyError("Blacklist configuration is missing in the config file.")
        return config["blacklists"]

    @staticmethod
    def generate_task_list(ip_list, blacklist_list):
        """
        Generates all possible tasks for given IPs and blacklists.

        Args:
            ip_list (list): List of /32 IP addresses.
            blacklist_list (list): List of blacklist configurations.

        Returns:
            list: A list of dictionaries representing tasks.
        """
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
        return task_list
