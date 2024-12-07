import asyncio
import signal
import time
from database.db_manager import DBManager
from tests.tests import run_tests
from utils.config_manager import load_config
from utils.display import Display, console
from utils.task_generator import TaskGenerator
from utils.task_synchronizer import TaskSynchronizer
from utils.process_manager import ProcessManager
from rich.table import Table
from logB.logger import Logger


def signal_handler(sig, frame):
    """
    Handles the SIGINT signal (CTRL+C) to exit gracefully.
    """
    logger = Logger(log_file_path="logs/application.log")
    logger.info("Application interrupted. Exiting...")
    display = Display()
    display.print_error("❌ Application interrupted. Exiting...")
    exit(0)


signal.signal(signal.SIGINT, signal_handler)


async def main():
    """
    Main function to initialize the application and handle its lifecycle.
    """
    logger = Logger(log_file_path="logs/application.log")
    display = Display()

    # Run system tests
    try:
        display.print_header()
        time.sleep(2)
        display.print_section_header("System Tests")

        test_results = run_tests()
        table = Table(title="Test Results")
        table.add_column("Test Name", justify="left", style="cyan", no_wrap=True)
        table.add_column("Result", style="green")

        for result in test_results:
            test_name, result_status = result
            result_style = "red" if result_status != "Passed" else "green"
            table.add_row(test_name, result_status, style=result_style)

        console.print(table)
        display.print_success("All system tests completed.")
    except Exception as e:
        logger.error(f"System tests failed: {e}")
        display.print_error(f"❌ System tests failed: {e}")
        return

    # Load configuration
    try:
        config = load_config()
        if not config:
            raise ValueError("Configuration could not be loaded.")
        logger.info("Configuration loaded successfully.")
        display.print_success("✔️ Configuration loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        display.print_error(f"❌ Failed to load configuration: {e}")
        return

    # Generate tasks
    try:
        ip_list = TaskGenerator.parse_ip_list("data/netconf_24_prefixes.yaml")
        blacklist_list = TaskGenerator.get_blacklist_config()
        in_memory_tasks = TaskGenerator.generate_task_list(ip_list, blacklist_list)

        if in_memory_tasks:
            logger.info(f"Generated {len(in_memory_tasks)} tasks.")
            display.print_success(f"✔️ Total tasks generated: {len(in_memory_tasks)}")
        else:
            raise ValueError("No tasks were generated.")
    except Exception as e:
        logger.error(f"Task generation failed: {e}")
        display.print_error(f"❌ Task generation failed: {e}")
        return

    # Initialize DBManager
    try:
        db_manager = DBManager(config)
        logger.info("DBManager initialized successfully.")
        display.print_success("✔️ DBManager initialized successfully.")
    except Exception as e:
        logger.error(f"DBManager initialization failed: {e}")
        display.print_error(f"❌ DBManager initialization failed: {e}")
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

        await synchronizer.synchronize()
        logger.info("Task synchronization completed.")
        display.print_success("✔️ Task synchronization completed.")
    except Exception as e:
        logger.error(f"Task synchronization failed: {e}")
        display.print_error(f"❌ Task synchronization failed: {e}")
        return

    # Process tasks dynamically
    try:
        process_manager = ProcessManager(
            rabbitmq=db_manager.rabbitmq,
            sqlite_manager=db_manager.sqlite_db,
            config=config
        )
        queue_name = config["rabbitmq"].get("default_queue", "default_queue")
        await process_manager.fetch_and_process_tasks(queue_name)
        logger.info("Task processing completed.")
        display.print_success("✔️ Task processing completed.")
    except Exception as e:
        logger.error(f"Task processing failed: {e}")
        display.print_error(f"❌ Task processing failed: {e}")
        return


if __name__ == "__main__":
    asyncio.run(main())
