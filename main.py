import signal
import time

from rich.table import Table

from database.db_manager import DBManager
from tests.tests import run_tests
from utils import config_manager
from utils.display import Display, console


def signal_handler(sig, frame):
    """
    Handles the SIGINT signal (CTRL+C).
    """
    print("Exiting...")
    exit(0)


signal.signal(signal.SIGINT, signal_handler)


def main():
    """
    Runs the tests and displays the results in a table.
    """
    display = Display()
    display.print_header()
    time.sleep(2)
    display.print_section_header("System Tests")
    # Run tests and get results
    test_results = run_tests()

    # Create the table
    table = Table(title="Test Results")
    table.add_column("Test Name", justify="left", style="cyan", no_wrap=True)
    table.add_column("Result", style="green")

    # Add test results to the table
    for result in test_results:
        test_name, result_status = result  # Assuming result is a tuple (name, status)
        result_style = "red" if result_status == "Passed" else "green"  # Corrected line!
        table.add_row(test_name, result_status, style=result_style)

    # Print the table
    console.print(table)

    config = config_manager.load_config()
    sqlite_db = Database(config["sqlite"]["db_path"])
    sqlite_db.connect()
    rabbitmq = RabbitMQ(config["rabbitmq"]["host"])
    rabbitmq.connect()
    postgresql = PostgreSQL(host=config["postgresql"]["host"],database=config["postgresql"]["database"],user=config["postgresql"]["user"],password=config["postgresql"]["password"])
    postgresql.connect()

    # Initialize DBManager
    db_manager = DBManager(config, sqlite_db, rabbitmq, postgresql)  # Argümanları ilet
    db_manager.start()  # Perform startup tasks

    display.print_success("All system tests completed.")
    display.print_info("Press CTRL+C to exit...")

    # Keep the application running and connections alive
    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()