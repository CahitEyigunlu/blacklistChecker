import signal
import time
from database.db_manager import DBManager
from tests.tests import run_tests
from utils.config_manager import load_config
from utils.display import Display, console
from utils.task_generator import TaskGenerator
from utils.task_synchronizer import TaskSynchronizer  # TaskSynchronizer sınıfı
from rich.table import Table
from logB.logger import Logger


def signal_handler(sig, frame):
    """
    Handles the SIGINT signal (CTRL+C) to exit gracefully.
    """
    logger = Logger(log_file_path="logs/application.log")  # Local logger
    logger.info("Application interrupted. Exiting...")
    print("❌ Application interrupted. Exiting...")
    exit(0)


signal.signal(signal.SIGINT, signal_handler)


def main():
    """
    Main function to initialize the application and handle its lifecycle.
    """
    logger = Logger(log_file_path="logs/application.log")  # Logger instance
    display = Display()

    try:
        display.print_header()
        time.sleep(2)
        display.print_section_header("System Tests")

        # Run system tests and display results
        test_results = run_tests()
        table = Table(title="Test Results")
        table.add_column("Test Name", justify="left", style="cyan", no_wrap=True)
        table.add_column("Result", style="green")

        for result in test_results:
            test_name, result_status = result
            result_style = "red" if result_status == "Passed" else "green"
            table.add_row(test_name, result_status, style=result_style)

        console.print(table)
        display.print_success("All system tests completed.")
    except Exception as e:
        logger.error(f"System tests failed: {e}")
        print(f"❌ System tests failed: {e}")
        return

    # Load configuration
    try:
        config = load_config()
        if not config:
            raise ValueError("Configuration could not be loaded.")
        logger.info("Configuration loaded successfully.")
        print("✔️ Configuration loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        print(f"❌ Failed to load configuration: {e}")
        return

    # Generate tasks
    try:
        ip_list = TaskGenerator.parse_ip_list("data/netconf_24_prefixes.yaml")
        blacklist_list = TaskGenerator.get_blacklist_config()
        in_memory_tasks = TaskGenerator.generate_task_list(ip_list, blacklist_list)

        if in_memory_tasks:
            logger.info(f"Generated {len(in_memory_tasks)} tasks.")
            print(f"✔️ Total tasks generated: {len(in_memory_tasks)}")
        else:
            raise ValueError("No tasks were generated.")
    except Exception as e:
        logger.error(f"Task generation failed: {e}")
        print(f"❌ Task generation failed: {e}")
        return

    # Initialize DBManager
    try:
        db_manager = DBManager(config)
        logger.info("DBManager initialized successfully.")
        print("✔️ DBManager initialized successfully.")
    except Exception as e:
        logger.error(f"DBManager initialization failed: {e}")
        print(f"❌ DBManager initialization failed: {e}")
        return

    # Synchronize tasks
    try:
        synchronizer = TaskSynchronizer(
            sqlite_manager=db_manager.sqlite_db,
            rabbitmq=db_manager.rabbitmq,
            in_memory_tasks=in_memory_tasks,
            config=config,
            active_db_manager=db_manager  
        )
        synchronizer.synchronize()
        task_statuses = synchronizer.report_status()
        print(f"Task Status Report: {task_statuses}")
        logger.info(f"Task synchronization completed: {task_statuses}")
    except Exception as e:
        logger.error(f"Task synchronization failed: {e}")
        print(f"❌ Task synchronization failed: {e}")
        return


    try:
        logger.info("Starting application...")
        db_manager.start()

        display.print_info("Application is running. Press CTRL+C to exit...")
        while True:
            time.sleep(1)  # Keep the application alive

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"❌ Unexpected error: {e}")
    finally:
        logger.info("Closing all database connections...")
        db_manager.close_connections()
        display.print_success("All connections closed. Application terminated.")
        print("✔️ All connections closed. Application terminated.")


if __name__ == "__main__":
    main()

