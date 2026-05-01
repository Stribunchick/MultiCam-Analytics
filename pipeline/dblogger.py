import sqlite3
import multiprocessing
from queue import Empty
import time

class DBLogger(multiprocessing.Process):
    def __init__(self, DB_PATH, log_queue):
        super().__init__()
        self.db_path = DB_PATH
        self.log_queue = log_queue
        self.stop_evt = multiprocessing.Event()

    @staticmethod
    def _configure_connection(conn):
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA temp_store=MEMORY;")
        conn.execute("PRAGMA busy_timeout = 10000;")

    def init_logs(self):
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        self._configure_connection(conn)
        c = conn.cursor()
        c.execute("""
CREATE TABLE IF NOT EXISTS logs(
                  id TEXT,
                  cam_id INTEGER,
                  datetimeStart TEXT,
                  datetimeStop TEXT,
                  event_type TEXT,
                  src TEXT,
                  FOREIGN KEY(cam_id) REFERENCES cameras(id)
                  )
""")    
        conn.commit()
        conn.close()

    def start_action(self, log_id, cam_id, dtStart, etype, src):
        # Один INSERT с выборкой location из cameras
        self.cursor.execute("""
            INSERT INTO logs(id, cam_id, datetimeStart, event_type, src)
            VALUES (?, ?, ?, ?, ?)
        """, (log_id, cam_id, dtStart, etype, src))
        

    def stop_action(self, log_id, dtStop):
        # UPDATE вместо INSERT
        self.cursor.execute("""
            UPDATE logs
            SET datetimeStop = ?
            WHERE id = ?
        """, (dtStop, log_id))

    def run(self):
        self.conn = sqlite3.connect(self.db_path, timeout=10.0, check_same_thread=False)
        self._configure_connection(self.conn)
        self.cursor = self.conn.cursor()

        BATCH_SIZE = 100      # коммитим каждые 100 записей
        COMMIT_INTERVAL = 0.25
        pending = 0
        last_commit_at = time.monotonic()

        while not self.stop_evt.is_set():
            try:
                task = self.log_queue.get(timeout=0.1)
            except Empty:
                if pending and (time.monotonic() - last_commit_at) >= COMMIT_INTERVAL:
                    self.conn.commit()
                    pending = 0
                    last_commit_at = time.monotonic()
                continue

            action = task["action"]
            if action == "start":
                log_id = task["id"]
                cam_id = task["cam_id"]
                dtStart = task["datetimeStart"]
                etype = task["event_type"]
                src = task["src"]
                self.start_action(log_id, cam_id, dtStart, etype, src)
            elif action == "end":
                log_id = task["log_id"]
                dtStop = task["datetimeStop"]
                self.stop_action(log_id, dtStop)

            pending += 1
            if pending >= BATCH_SIZE or (time.monotonic() - last_commit_at) >= COMMIT_INTERVAL:
                self.conn.commit()
                pending = 0
                last_commit_at = time.monotonic()

        # Финальный коммит при остановке
        self.conn.commit()
        self.conn.close()

    def stop(self):
        self.stop_evt.set()

if __name__ == "__main__":
    a = DBLogger("./db/logs.db", None)
    a.init_logs()
