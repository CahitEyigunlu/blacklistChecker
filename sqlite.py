import sqlite3
from threading import Lock

class SQLiteTaskManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.lock = Lock()

    def delete_completed_task(self, task_id):
        """
        Verilen görev ID'sine göre tamamlanmış görevi siler.
        """
        with self.lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
                conn.commit()
                conn.close()
                print(f"Görev silindi: {task_id}")
            except sqlite3.Error as e:
                print(f"SQLite hata: {str(e)}")
