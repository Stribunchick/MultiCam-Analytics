import multiprocessing
import sqlite3
import time
from queue import Empty


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

    @staticmethod
    def _ensure_logs_schema(cursor):
        cursor.execute("""
CREATE TABLE IF NOT EXISTS logs(
                  id TEXT,
                  cam_id INTEGER,
                  datetimeStart TEXT,
                  datetimeStop TEXT,
                  event_type TEXT,
                  src TEXT,
                  snapshot_path TEXT,
                  FOREIGN KEY(cam_id) REFERENCES cameras(id)
                  )
""")
        cursor.execute("PRAGMA table_info(logs)")
        columns = {row[1] for row in cursor.fetchall()}
        if "snapshot_path" not in columns:
            cursor.execute("""
                ALTER TABLE logs
                ADD COLUMN snapshot_path TEXT
            """)

    def init_logs(self):
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        self._configure_connection(conn)
        cursor = conn.cursor()
        self._ensure_logs_schema(cursor)
        conn.commit()
        conn.close()

    def start_action(self, log_id, cam_id, dt_start, event_type, src, snapshot_path):
        self.cursor.execute("""
            INSERT INTO logs(id, cam_id, datetimeStart, event_type, src, snapshot_path)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (log_id, cam_id, dt_start, event_type, src, snapshot_path))

    def stop_action(self, log_id, dt_stop):
        self.cursor.execute("""
            UPDATE logs
            SET datetimeStop = ?
            WHERE id = ?
        """, (dt_stop, log_id))

    def snapshot_action(self, log_id, snapshot_path):
        self.cursor.execute("""
            UPDATE logs
            SET snapshot_path = ?
            WHERE id = ?
        """, (snapshot_path, log_id))

    def run(self):
        self.conn = sqlite3.connect(self.db_path, timeout=10.0, check_same_thread=False)
        self._configure_connection(self.conn)
        self.cursor = self.conn.cursor()
        self._ensure_logs_schema(self.cursor)

        batch_size = 100
        commit_interval = 0.25
        pending = 0
        last_commit_at = time.monotonic()

        while True:
            try:
                task = self.log_queue.get(timeout=0.1)
            except Empty:
                if pending and (time.monotonic() - last_commit_at) >= commit_interval:
                    self.conn.commit()
                    pending = 0
                    last_commit_at = time.monotonic()
                if self.stop_evt.is_set():
                    break
                continue

            if task is None:
                break

            action = task["action"]
            if action == "start":
                self.start_action(
                    task["id"],
                    task["cam_id"],
                    task["datetimeStart"],
                    task["event_type"],
                    task["src"],
                    task.get("snapshot_path"),
                )
            elif action == "snapshot":
                self.snapshot_action(
                    task["log_id"],
                    task.get("snapshot_path"),
                )
            elif action == "end":
                self.stop_action(task["log_id"], task["datetimeStop"])

            pending += 1
            if pending >= batch_size or (time.monotonic() - last_commit_at) >= commit_interval:
                self.conn.commit()
                pending = 0
                last_commit_at = time.monotonic()

        self.conn.commit()
        self.conn.close()

    def stop(self):
        self.stop_evt.set()
        try:
            self.log_queue.put_nowait(None)
        except Exception:
            pass


if __name__ == "__main__":
    a = DBLogger("./db/logs.db", None)
    a.init_logs()
