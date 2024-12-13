# Blacklist Checker

![Logo](https://raw.githubusercontent.com/CahitEyigunlu/blacklistChecker/refs/heads/main/assets/logo.webp)

## Introduction

The Blacklist Checker is a tool designed to monitor and verify blacklisted domains, IPs, or other entities using a customizable configuration. It offers logging, database management, and task synchronization for efficient operation.

This tool leverages asynchronous programming and a message queue (RabbitMQ) to efficiently process a large number of IP addresses against multiple blacklists concurrently. Results can be stored in various databases like PostgreSQL or MongoDB for further analysis and reporting.

## Features

- Dynamic configuration via `.env`, `blacklist.yml`, and `netconf_24_prefixes.yaml`.
- Graceful handling of application interruptions.
- Robust logging and error management.
- Extensible module-based architecture for database, tasks, and display.
- Asynchronous task processing with RabbitMQ for high performance.
- Support for multiple database backends (SQLite, PostgreSQL, MongoDB).
- Scalable to handle a large number of IP addresses and blacklists.

## Setup

### Requirements

- Python 3.10+
- Docker (optional, for containerized deployment)
- Required packages in `requirements.txt` (Install with `pip install -r requirements.txt`)

### Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/cahit.eyigunlu/blacklistChecker.git
   cd blacklistChecker
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure the environment:**

   - Copy the `.env.example` file to `.env` and fill in the required values.
     ```bash
     cp .env.example .env
     ```
     - See the **Environment Configuration** section below for details.

   - Configure blacklist sources in `blacklist.yml`.
     - See the **Blacklist Configuration (`blacklist.yml`)** section for details.

   - Provide the IP prefixes to be checked in `netconf_24_prefixes.yaml`.
     - See the **IP Prefix Configuration (`netconf_24_prefixes.yaml`)** section for details.

## Environment Configuration

The project uses a `.env` file to manage environment variables. Here is an example structure with sensitive information redacted:

```
# MongoDB Settings
MONGO_URL="mongodb+srv://<user>:<password>@<cluster-address>/<database-name>?..."
MONGO_DB_NAME="..."

# RabbitMQ Settings
RABBITMQ_HOST="..."
RABBITMQ_PORT=5672
RABBITMQ_USERNAME="..."
RABBITMQ_PASSWORD="..."  # Set as an environment variable
RABBITMQ_ERLANG_COOKIE="..."  # Store on the RabbitMQ server
RABBITMQ_WEB_UI_PORT=...
RABBITMQ_AMQP_PORT=...
RABBITMQ_DEFAULT_QUEUE="..."
RABBITMQ_CONCURRENCY_LIMIT=...

# PostgreSQL Settings
POSTGRES_USERNAME="..."
POSTGRES_PASSWORD="..."  # Set as an environment variable
POSTGRES_DB="..."
POSTGRES_HOST="..."
POSTGRES_PORT=...

APP_LOG_PATH=...
ERROR_LOG_PATH=...
```

- **Important:** For security, do not store sensitive information like passwords and API keys directly in the `.env` file. Instead, use environment variables or a secrets management tool.

## Blacklist Configuration (`blacklist.yml`)

 This file defines the blacklist providers to be used for checking. Here's an example structure:

```yaml
database:
  recorded_dbs:
    mongodb: false
    mysql: false  
    postgresql: true

# SQLite Settings (if used)
sqlite:
  db_path: "state.db"  # Path to the SQLite database file

# Blacklist Services
blacklists:
  - name: "Spamhaus"
    dns: "zen.spamhaus.org"
    removal_link: "https://www.spamhaus.org/removal/"
    removal_method: "Web form submission"
  - name: "Barracuda"
    # ... other blacklist providers ...
```

You can add or remove blacklist providers as needed.

## IP Prefix Configuration (`netconf_24_prefixes.yaml`)

This file contains a list of IP prefixes (in CIDR notation) that will be checked against the blacklists. Here's an example:

```yaml
- 37.123.97.0/24
- 37.123.99.0/24
- 37.123.100.0/24
- 45.150.9.0/24
```

You can add as many IP prefixes as you need.

## Usage

1. **Run the main application:**

   ```bash
   python main.py
   ```

2. **Use `CTRL+C` to gracefully exit the application.**

## Dockerized Deployment

You can also run the application in a Docker container.

1. **Initialize Docker Swarm (required for Secrets):**
   ```bash
   docker swarm init
   ```

2. **Add Docker Secrets:**
   ```bash
   echo "your_rabbitmq_password" | docker secret create rabbitmq_password -
   echo "your_rabbitmq_cookie" | docker secret create rabbitmq_erlang_cookie -
   echo "your_postgres_password" | docker secret create postgres_password -
   ```

3. **Build the Docker image:**

   ```bash
   docker build -t blacklist-checker .
   ```

4. **Run the Docker container:**

   ```bash
   docker run -it blacklist-checker
   ```

5. **Using Docker Compose:**
   If you have `docker-compose.yml` configured, you can start the application with:

   ```bash
   docker-compose up -d
   ```

   Make sure to initialize Docker Swarm and add required secrets before starting.

## Testing

Run the test suite to ensure functionality:

```bash
python -m unittest discover -s tests
```

## Project Structure

- **main.py**: Entry point of the application.
- **database/**: Handles database operations.
- **utils/**: Utility functions including configuration and task management.
- **logs/**: Contains application logs.
- **tests/**: Unit tests for modules.
- **doc/**: Contains documentation files.

## Technology Choices

- **SQLite and RabbitMQ:** SQLite is used as a lightweight, file-based database for managing the application state and queueing tasks. RabbitMQ acts as a message broker to distribute tasks efficiently among workers, enabling asynchronous processing and improving performance.

- **PostgreSQL/MongoDB:**  These databases provide more robust and scalable options for storing the blacklist check results. They offer better performance for large datasets and more advanced querying capabilities.

- **Asynchronous Programming:**  By using asynchronous programming with `asyncio`, the application can handle multiple blacklist checks concurrently without blocking, leading to significant performance gains, especially when dealing with a large number of IP addresses.

## Future Enhancements

- Add support for more blacklist providers.
- Improve reporting and visualization.
- Implement a web interface for easier monitoring and management.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

