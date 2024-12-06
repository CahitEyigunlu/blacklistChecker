# blacklistChecker

`blacklistChecker` is a Python script designed to check if a specific IP address or a list of IP addresses appears on various blacklists.

## Features

- Supports multiple blacklist services (e.g., Spamhaus, Barracuda, SORBS).
- Allows checking a single IP address or a list of IP addresses.
- Provides additional information for blacklisted IPs, such as removal links and methods.
- Easily configurable using a YAML-based configuration file.
- Logs the results and activities for audit and debugging purposes.

## Requirements

- Python 3.8 or higher
- Required dependencies listed in `requirements.txt`

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/CahitEyigunlu/blacklistChecker.git
   cd blacklistChecker
   ```

2. Install the required Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure your environment by creating and editing a `.env` file.

## Environment Configuration (`.env`)

The `.env` file is used to store environment variables and sensitive configurations. Below is an example of how your `.env` file should look:

```plaintext
# Database configurations
DB_HOST=localhost
DB_PORT=5432
DB_USER=your_database_user
DB_PASSWORD=your_database_password

# Logging level (INFO, DEBUG, etc.)
LOG_LEVEL=INFO

# API Keys for external services (if any)
API_KEY_SPAMHAUS=your_spamhaus_api_key
API_KEY_SORBS=your_sorbs_api_key

# Application settings
APP_ENV=development
APP_DEBUG=True
```

- `DB_HOST`, `DB_PORT`, `DB_USER`, and `DB_PASSWORD`: Specify database connection settings if a database is used.
- `LOG_LEVEL`: Determines the verbosity of logs.
- `API_KEY_*`: Placeholder for API keys for external blacklist services.
- `APP_ENV`: Specifies the environment (`development` or `production`).
- `APP_DEBUG`: Enables or disables debug mode.

## Usage

### Checking a Single IP Address
Run the following command:
```bash
python main.py --ip <IP_ADDRESS>
```

### Checking a List of IP Addresses
Prepare a file containing the IP addresses (one per line) and use:
```bash
python main.py --file <FILE_PATH>
```

### Output
The results will indicate whether an IP address is blacklisted and, if applicable, provide details about the blacklist entry and removal instructions.

## Configuration

- `blacklist.yml`: Contains the configuration for supported blacklist services. You can customize it by adding new blacklists or modifying existing ones.

## Logs

All logs are stored in the `logs` directory. These logs provide insights into the script's operation and can be used for debugging or auditing purposes.

## Testing

Run unit tests with:
```bash
pytest tests/
```

## Project Structure

```plaintext
blacklistChecker/
├── blacklist_checkers/  # Modules for interacting with various blacklist APIs
├── database/            # Database-related files
├── logs/                # Logs directory
├── tests/               # Unit tests
├── utils/               # Utility scripts
├── blacklist.yml        # Configuration for blacklist services
├── main.py              # Main script entry point
├── README.md            # Project documentation
├── LICENSE              # License file
└── requirements.txt     # Python dependencies
```

## Logo
![Project Logo](https://raw.githubusercontent.com/CahitEyigunlu/blacklistChecker/main/logo.webp)

## License

This project is licensed under the MIT License. See the `LICENSE` file for more details.

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests to improve this project.

---

For more details, visit the [GitHub repository](https://github.com/CahitEyigunlu/blacklistChecker).
```

