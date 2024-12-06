
![Project Logo](https://raw.githubusercontent.com/CahitEyigunlu/blacklistChecker/main/logo.webp)


```markdown
# Blacklist Checker

## Introduction
The Blacklist Checker is a tool designed to monitor and verify blacklisted domains, IPs, or other entities using a customizable configuration. It offers logging, database management, and task synchronization for efficient operation.

## Features
- Dynamic configuration via `.env` and `blacklist.yml`.
- Graceful handling of application interruptions.
- Robust logging and error management.
- Extensible module-based architecture for database, tasks, and display.

## Setup

### Requirements
- Python 3.8+
- Required packages in `requirements.txt` (Install with `pip install -r requirements.txt`)

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/cahit.eyigunlu/blacklistChecker.git
   cd blacklistChecker
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure the `.env` file (See Environment Configuration).

## Environment Configuration
The project uses a `.env` file to manage environment variables. Here is an example structure:

```
DATABASE_URL=sqlite:///state.db
LOG_LEVEL=INFO
BLACKLIST_SOURCE=blacklist.yml
API_KEY=your_api_key_here
```

- `DATABASE_URL`: Path to the database file.
- `LOG_LEVEL`: Logging level (e.g., DEBUG, INFO, WARNING, ERROR).
- `BLACKLIST_SOURCE`: Path to the blacklist configuration file.
- `API_KEY`: API key for any external services used.

To create your own `.env` file, copy the example:
```bash
cp .env.example .env
```

Update the values as per your setup.

## Usage
1. Run the main application:
   ```bash
   python main.py
   ```
2. Use `CTRL+C` to gracefully exit the application.

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

## Future Enhancements
- Add support for more blacklist providers.
- Improve reporting and visualization.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
```

Bunu GitHub projenizde README dosyası olarak kullanabilirsiniz. Başka bir konuda yardımcı olmamı ister misiniz?