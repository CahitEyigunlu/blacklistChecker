import asyncio
import signal
import time
from database.db_manager import DBManager
from database.postgre import PostgreSQL
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
    display = Display()
    display.print_error("\u274c Application interrupted. Exiting...")
    exit(0)

async def main():
    """
    Main function to initialize the application and handle its lifecycle.
    """
    # Load configuration
    try:
        config = load_config()
        if not config:
            raise ValueError("Configuration could not be loaded.")
    except Exception as e:
        print(f"\u274c Failed to load configuration: {e}")
        return

    # Initialize logger with dynamic log path
    logger = Logger(log_file_path=config['logging']['app_log_path'])
    display = Display()

    # Signal Handling
    signal.signal(signal.SIGINT, signal_handler)

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
        display.print_success("\u2714\ufe0f All system tests completed.")
    except Exception as e:
        logger.error(f"System tests failed: {e}", extra={"function": "main", "section": "system_tests"})
        display.print_error(f"\u274c System tests failed: {e}")
        return

    # Generate tasks
    try:
        task_generator = TaskGenerator()
        ip_list = task_generator.parse_ip_list("data/netconf_24_prefixes.yaml")
        blacklist_list = task_generator.get_blacklist_config()
        in_memory_tasks = task_generator.generate_task_list(ip_list, blacklist_list)

        if in_memory_tasks:
            logger.info(f"Generated {len(in_memory_tasks)} tasks.")
            display.print_success(f"\u2714\ufe0f Total tasks generated: {len(in_memory_tasks)}")
        else:
            raise ValueError("No tasks were generated.")
    except Exception as e:
        logger.error(f"Task generation failed: {e}", extra={"function": "main", "section": "task_generation"})
        display.print_error(f"\u274c Task generation failed: {e}")
        return

    
    # Initialize DBManager
    try:
        db_manager = DBManager(config)
        logger.info("DBManager initialized successfully.")
        display.print_success("\u2714\ufe0f DBManager initialized successfully.")
    except Exception as e:
        logger.error(f"DBManager initialization failed: {e}", extra={"function": "main", "section": "db_init"})
        display.print_error(f"\u274c DBManager initialization failed: {e}")
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
        display.print_success("\u2714\ufe0f Task synchronization completed.")
    except Exception as e:
        logger.error(f"Task synchronization failed: {e}", extra={"function": "main", "section": "task_sync"})
        display.print_error(f"\u274c Task synchronization failed: {e}")
        return

    # Process tasks dynamically
    try:
        process_manager = ProcessManager(
            rabbitmq=db_manager.rabbitmq,
            sqlite_manager=db_manager.sqlite_db,
            config=config
        )
        queue_name = config["rabbitmq"]["default_queue"]
        await process_manager.fetch_and_process_tasks(queue_name)
        logger.info("Task processing completed.")
        display.print_success("\u2714\ufe0f Task processing completed.")
    except Exception as e:
        logger.error(f"Task processing failed: {e}", extra={"function": "main", "section": "task_processing"})
        display.print_error(f"\u274c Task processing failed: {e}")
        return
        

    # Finalize and handle PostgreSQL processing
    try:
        postgres = PostgreSQL(config)
        sqlite_manager = db_manager.sqlite_db  # Access SQLite TaskManager instance
        postgres.process_sqlite_to_postgres_and_exit(sqlite_manager)
        logger.info("SQLite to PostgreSQL processing and cleanup completed.")
        display.print_success("✔️ SQLite to PostgreSQL processing and cleanup completed.")
    except Exception as e:
        logger.error(f"SQLite to PostgreSQL processing failed: {e}", extra={"function": "main", "section": "postgres_processing"})
        display.print_error(f"❌ SQLite to PostgreSQL processing failed: {e}")
        return


if __name__ == "__main__":
    asyncio.run(main())
