class TaskSynchronizer:
    """
    Synchronizes tasks between in-memory tasks, SQLite, and RabbitMQ.
    """

    def __init__(self, sqlite_manager, rabbitmq, in_memory_tasks, config):
        """
        Initializes the TaskSynchronizer.

        Args:
            sqlite_manager (TaskManager): SQLite manager instance.
            rabbitmq (RabbitMQ): RabbitMQ manager instance.
            in_memory_tasks (list): List of in-memory tasks (combinations).
            config (dict): Configuration dictionary.
        """
        self.sqlite_manager = sqlite_manager
        self.rabbitmq = rabbitmq
        self.in_memory_tasks = in_memory_tasks
        self.config = config

    def synchronize(self):
        """
        Synchronizes in-memory tasks with SQLite and RabbitMQ.
        """
        # Fetch SQLite tasks
        sqlite_tasks = self.sqlite_manager.fetch_pending_tasks()
        sqlite_task_set = set((task[1], task[2]) for task in sqlite_tasks)  # (ip_address, blacklist_name)

        # Fetch RabbitMQ tasks
        queue_name = self.config["rabbitmq"].get("default_queue", "default_queue")
        rabbitmq_tasks = self.rabbitmq.get_all_tasks(queue_name=queue_name)
        rabbitmq_task_set = set((task["ip"], task["blacklist_name"]) for task in rabbitmq_tasks)

        # Convert in-memory tasks to a comparable format
        in_memory_task_set = set((task["ip"], task["blacklist_name"]) for task in self.in_memory_tasks)

        # Find missing tasks in SQLite
        missing_in_sqlite = in_memory_task_set - sqlite_task_set

        # Add missing tasks to SQLite
        for ip, blacklist_name in missing_in_sqlite:
            self.sqlite_manager.insert_tasks([{
                "ip": ip,
                "blacklist_name": blacklist_name
            }])
            print(f"✔️ Task added to SQLite: {ip}, {blacklist_name}")

        # Find missing tasks in RabbitMQ
        missing_in_rabbitmq = in_memory_task_set - rabbitmq_task_set

        # Add missing tasks to RabbitMQ
        for ip, blacklist_name in missing_in_rabbitmq:
            self.rabbitmq.publish_task({
                "ip": ip,
                "blacklist_name": blacklist_name
            })
            print(f"✔️ Task added to RabbitMQ: {ip}, {blacklist_name}")

    def report_status(self):
        """
        Reports the status of tasks across sources.

        Returns:
            dict: A report of task statuses.
        """
        pending_tasks = len(self.sqlite_manager.fetch_pending_tasks())
        queue_name = self.config["rabbitmq"].get("default_queue", "default_queue")
        rabbitmq_queue_size = self.rabbitmq.queue_size(queue_name=queue_name)
        total_in_memory = len(self.in_memory_tasks)

        return {
            "total_in_memory": total_in_memory,
            "pending_in_sqlite": pending_tasks,
            "rabbitmq_queue_size": rabbitmq_queue_size
        }
