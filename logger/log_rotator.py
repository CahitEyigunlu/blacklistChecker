import os
import shutil
from datetime import datetime, timedelta
from logger.config import LOG_FILE_PATH, LOG_ROTATION_SIZE, LOG_RETENTION_DAYS

def rotate_log():
    """
    Rotates the log file if it exceeds the defined size limit.
    Renames the current log file with a timestamp and creates a new empty log file.
    """
    # Kontrol: Log dosyası belirlenen boyut sınırını aşıyor mu?
    if os.path.exists(LOG_FILE_PATH) and os.path.getsize(LOG_FILE_PATH) > LOG_ROTATION_SIZE:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        archived_log_path = f"{LOG_FILE_PATH}.{timestamp}.backup"
        # Mevcut log dosyasını yeniden adlandır
        os.rename(LOG_FILE_PATH, archived_log_path)
        # Yeni, boş bir log dosyası oluştur
        with open(LOG_FILE_PATH, 'w') as new_log_file:
            new_log_file.write("")

def delete_old_logs():
    """
    Deletes log files that have exceeded the retention period.
    Searches for files with the .backup extension and deletes those older than the configured retention period.
    """
    retention_period = timedelta(days=LOG_RETENTION_DAYS)
    current_time = datetime.now()
    
    # Log dosyalarının bulunduğu dizin
    log_dir = os.path.dirname(LOG_FILE_PATH)
    for filename in os.listdir(log_dir):
        # Yalnızca .backup uzantısına sahip yedek log dosyalarını kontrol et
        if filename.startswith(os.path.basename(LOG_FILE_PATH)) and filename.endswith(".backup"):
            file_path = os.path.join(log_dir, filename)
            file_creation_time = datetime.fromtimestamp(os.path.getctime(file_path))
            # Saklama süresini aşan dosyaları sil
            if current_time - file_creation_time > retention_period:
                os.remove(file_path)

def manage_logs():
    """
    Main function to manage logs: rotates the log if needed and deletes old logs.
    This should be scheduled to run periodically to maintain log size and retention.
    """
    rotate_log()
    delete_old_logs()
