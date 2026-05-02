import sqlite3
# from UI_python.tools.config import Config

import os
import sys
from datetime import datetime

from PySide6.QtCore import QSize
from PySide6.QtWidgets import QApplication, QMainWindow, QTableView

class DBWorker:
    def __init__(self, db_path):
        db_dir = os.path.dirname(os.path.abspath(db_path))
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

        self.conn = sqlite3.connect(db_path, timeout=10.0)
        self._configure_connection()
        self.cur = self.conn.cursor()
        self.init_tables()

    def _configure_connection(self):
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.execute("PRAGMA journal_mode = WAL")
        self.conn.execute("PRAGMA synchronous = NORMAL")
        self.conn.execute("PRAGMA busy_timeout = 10000")

    def close(self):
        self.conn.close()
        

    def init_tables(self):

        """
        Init tables
        """

        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS configs (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                name TEXT,
                                cameras_per_row INTEGER,
                                enabled INTEGER,
                                conf_thresh REAL,
                                fps INTEGER
                                )
        """)

        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS cameras(
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                name TEXT,
                                location TEXT,
                                username TEXT,
                                password TEXT,
                                ip TEXT
                                )
        """)
        
        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS classes(
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                name TEXT,
                                model_id INTEGER,
                                danger_level TEXT NOT NULL DEFAULT 'safe',
                                alert_enabled INTEGER NOT NULL DEFAULT 1,
                                alert_delay_sec REAL NOT NULL DEFAULT 0,
                                FOREIGN KEY(model_id) REFERENCES models(id)
                                )
        """)

        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS models (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                model_path TEXT
                                )
        """)

        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS config_cameras (
                                config_id INTEGER NOT NULL,
                                cam_id INTEGER NOT NULL,
                                PRIMARY KEY (config_id, cam_id),
                                FOREIGN KEY (config_id) REFERENCES configs(id),
                                FOREIGN KEY (cam_id) REFERENCES cameras(id)
                                )
        """)
        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS config_classes (
                                config_id INTEGER NOT NULL,
                                class_id INTEGER NOT NULL,
                                PRIMARY KEY(config_id, class_id),
                                FOREIGN KEY(config_id) REFERENCES configs(id),
                                FOREIGN KEY(class_id) REFERENCES classes(id)
                                )
        """)

        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS camera_rois (
                                config_id INTEGER NOT NULL,
                                cam_id INTEGER NOT NULL,
                                x1 REAL NOT NULL,
                                y1 REAL NOT NULL,
                                x2 REAL NOT NULL,
                                y2 REAL NOT NULL,
                                updated_at TEXT,
                                PRIMARY KEY(config_id, cam_id),
                                FOREIGN KEY(config_id) REFERENCES configs(id),
                                FOREIGN KEY(cam_id) REFERENCES cameras(id)
                                )
        """)

        self.cur.execute("""
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

        self._ensure_classes_schema()
        self._ensure_logs_schema()
        self.conn.commit()

    def _ensure_classes_schema(self):
        self.cur.execute("PRAGMA table_info(classes)")
        columns = {row[1] for row in self.cur.fetchall()}
        if "danger_level" not in columns:
            self.cur.execute("""
                ALTER TABLE classes
                ADD COLUMN danger_level TEXT NOT NULL DEFAULT 'safe'
            """)
        if "alert_enabled" not in columns:
            self.cur.execute("""
                ALTER TABLE classes
                ADD COLUMN alert_enabled INTEGER NOT NULL DEFAULT 1
            """)
        if "alert_delay_sec" not in columns:
            self.cur.execute("""
                ALTER TABLE classes
                ADD COLUMN alert_delay_sec REAL NOT NULL DEFAULT 0
            """)

    def _ensure_logs_schema(self):
        self.cur.execute("PRAGMA table_info(logs)")
        columns = {row[1] for row in self.cur.fetchall()}
        if "snapshot_path" not in columns:
            self.cur.execute("""
                ALTER TABLE logs
                ADD COLUMN snapshot_path TEXT
            """)

    def fetch_all_configs(self):
        self.cur.execute("""
                SELECT id, name FROM configs;
        """)
        configs = self.cur.fetchall()
        return configs

    def fetch_config_by_id(self, config_id):
        """
        do stuff
        """
        self.cur.execute("""
                SELECT * FROM configs WHERE id = ?
        """, (config_id,))
        config = self.cur.fetchall()
        return config

    

    def edit_config(self, config_id, data):
        self.cur.execute("""
            UPDATE configs 
            SET name = ?, cameras_per_row = ?, enabled = ?, conf_thresh = ?, fps = ?
            WHERE id = ?
        """, (data["name"], data["cameras_per_row"], data["enabled"], data["conf_thres"], data["fps"], config_id,))
        
        self.conn.commit()


    def delete_config(self, config_id):

        """
        Удалить конфиг и все связи CASCADE?
        """

        try:
            self.cur.execute("""
                DELETE FROM camera_rois WHERE config_id = ?
            """, (config_id,))
            self.cur.execute("""
                DELETE FROM config_cameras WHERE config_id = ?
            """, (config_id,))
            self.cur.execute("""
                DELETE FROM config_classes WHERE config_id = ?
            """, (config_id,))
            self.cur.execute("""
                DELETE FROM configs WHERE id = ?
            """, (config_id,))
            self.conn.commit()
        except sqlite3.Error:
            self.conn.rollback()
            raise

    def delete_camera(self, camera_id):

        """
        Удалить камеру и все связи CASCADE?
        """
        self.cur.execute("""
        DELETE FROM camera_rois WHERE cam_id = ?
        """, (camera_id,))

        self.cur.execute("""
        DELETE FROM config_cameras WHERE cam_id = ?
        """, (camera_id,))

        self.cur.execute("""
                DELETE FROM cameras WHERE id = ?
        """, (camera_id,))
        self.conn.commit()
    
    def fetch_cameras_by_id(self, config_id):
        self.cur.execute("""
            SELECT c.*
            FROM cameras c
            JOIN config_cameras cc ON c.id = cc.cam_id
            WHERE cc.config_id = ?
        """, (config_id,))
        return self.cur.fetchall()
    
    def fetch_classes_by_id(self, config_id):
        self.cur.execute("""
            SELECT c.id, c.name, c.model_id, c.danger_level, c.alert_enabled, c.alert_delay_sec
            FROM classes c
            JOIN config_classes cc ON c.id = cc.class_id
            WHERE cc.config_id = ?
        """, (config_id,))

        return self.cur.fetchall()

    def get_all_cameras(self):
        self.cur.execute("""
            SELECT id, name FROM cameras
        """)
        cameras = self.cur.fetchall()
        
        return cameras
    
    def fetch_camera_by_id(self, camera_id):
        self.cur.execute("""
            SELECT * FROM cameras WHERE id = ?
        """, (camera_id, ))
        return self.cur.fetchall()
    
    def edit_camera(self, camera_id, data):
        self.cur.execute("""
            UPDATE cameras 
            SET name = ?, location = ?, username = ?, password = ?, ip = ?
            WHERE id = ?
        """, (data["name"], data["location"], data["username"], data["password"], data["ip"], camera_id,))
        self.conn.commit()

    def add_config(self, data):
        self.cur.execute("""
            INSERT INTO configs (name, cameras_per_row, enabled, conf_thresh, fps) VALUES (?, ?, ?, ?, ?)
        """, (data["name"], data["cameras_per_row"], data["enabled"], data["conf_thres"], data["fps"],))
        self.conn.commit()
        return self.cur.lastrowid
    
    def add_camera(self, data):
        self.cur.execute("""
            INSERT INTO cameras (name, location, username, password, ip) VALUES (?, ?, ?, ?, ?)
        """, (data["name"], data["location"], data["username"], data["password"], data["ip"],))
        self.conn.commit()
        return
    
    def clear_config_cameras(self, config_id):
        self.cur.execute("""
            DELETE FROM config_cameras WHERE config_id = ?
        """, (config_id,))
        self.conn.commit()

    def add_camera_to_config(self, config_id, cam_id):
        query = "INSERT INTO config_cameras (config_id, cam_id) VALUES (?, ?)"
        self.cur.execute(query, (config_id, cam_id,))
        self.conn.commit()

    def clear_config_classes(self, config_id):
        self.cur.execute("""
            DELETE FROM config_classes WHERE config_id = ?
        """, (config_id,))
        self.conn.commit()

    def add_class_to_config(self, config_id, class_id):
        query = "INSERT INTO config_classes (config_id, class_id) VALUES (?, ?)"
        self.cur.execute(query, (config_id, class_id,))
        self.conn.commit()

    def get_all_classes(self):
        self.cur.execute("""
            SELECT id, name, model_id, danger_level, alert_enabled, alert_delay_sec FROM classes
        """)
        return self.cur.fetchall()

    def fetch_all_classes_with_models(self):
        self.cur.execute("""
            SELECT
                c.id,
                c.name,
                c.model_id,
                c.danger_level,
                c.alert_enabled,
                c.alert_delay_sec,
                COALESCE(m.model_path, '')
            FROM classes c
            LEFT JOIN models m ON m.id = c.model_id
            ORDER BY c.model_id, c.name
        """)
        return self.cur.fetchall()

    def fetch_class_by_id(self, class_id):
        self.cur.execute("""
            SELECT id, name, model_id, danger_level, alert_enabled, alert_delay_sec
            FROM classes
            WHERE id = ?
        """, (class_id,))
        return self.cur.fetchall()

    def add_model(self, model_path):
        self.cur.execute("""
            INSERT INTO models (model_path) VALUES (?)
        """, (model_path,))
        self.conn.commit()
        model_id = self.cur.lastrowid
        return model_id
    
    def add_class(self, name, model_id, danger_level="safe", alert_enabled=1, alert_delay_sec=0.0):
        self.cur.execute("""
            INSERT INTO classes (name, model_id, danger_level, alert_enabled, alert_delay_sec)
            VALUES (?, ?, ?, ?, ?)
        """, (name, model_id, danger_level, int(bool(alert_enabled)), float(alert_delay_sec)))
        self.conn.commit()

    def edit_class(self, class_id, data):
        self.cur.execute("""
            UPDATE classes
            SET name = ?, danger_level = ?, alert_enabled = ?, alert_delay_sec = ?
            WHERE id = ?
        """, (
            data["name"],
            data["danger_level"],
            int(bool(data["alert_enabled"])),
            float(data["alert_delay_sec"]),
            class_id,
        ))
        self.conn.commit()
    
    def load_models(self):
        self.cur.execute("""
        SELECT * FROM models
    """)
        return self.cur.fetchall()
    
    def delete_model(self, model_id):
    # удалить связи config_classes
        self.cur.execute("""
            DELETE FROM config_classes 
            WHERE class_id IN (
                SELECT id FROM classes WHERE model_id = ?
            )
        """, (model_id,))

        # удалить классы
        self.cur.execute("""
            DELETE FROM classes WHERE model_id = ?
        """, (model_id,))

        # удалить модель
        self.cur.execute("""
            DELETE FROM models WHERE id = ?
        """, (model_id,))

        self.conn.commit()
    
    def get_models_by_id(self, classes):
        models_ids = set()
        for cls in classes:
            models_ids.add(cls[2])
        models_ids = list(models_ids)
        if not models_ids:
            return []
        placeholders = ",".join("?" for _ in models_ids)
        query = f"SELECT id, model_path FROM models WHERE id IN ({placeholders})"
        self.cur.execute(query, tuple(models_ids))
        return self.cur.fetchall()

    def fetch_rois_by_config_id(self, config_id):
        self.cur.execute("""
            SELECT cam_id, x1, y1, x2, y2
            FROM camera_rois
            WHERE config_id = ?
        """, (config_id,))
        return {
            cam_id: (x1, y1, x2, y2)
            for cam_id, x1, y1, x2, y2 in self.cur.fetchall()
        }

    def save_roi(self, config_id, cam_id, roi):
        if roi is None:
            self.cur.execute("""
                DELETE FROM camera_rois
                WHERE config_id = ? AND cam_id = ?
            """, (config_id, cam_id))
            self.conn.commit()
            return

        x1, y1, x2, y2 = roi
        self.cur.execute("""
            INSERT INTO camera_rois(config_id, cam_id, x1, y1, x2, y2, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(config_id, cam_id) DO UPDATE SET
                x1 = excluded.x1,
                y1 = excluded.y1,
                x2 = excluded.x2,
                y2 = excluded.y2,
                updated_at = excluded.updated_at
        """, (
            config_id,
            cam_id,
            float(x1),
            float(y1),
            float(x2),
            float(y2),
            datetime.now().astimezone().isoformat(" ", "seconds"),
        ))
        self.conn.commit()

    def fetch_dashboard_events(
        self,
        start_dt=None,
        end_dt=None,
        camera_id=None,
        event_type=None,
        limit=None,
    ):
        query = """
            SELECT
                l.id,
                l.cam_id,
                COALESCE(c.name, ''),
                COALESCE(c.location, ''),
                l.datetimeStart,
                l.datetimeStop,
                l.event_type,
                l.src,
                l.snapshot_path
            FROM logs l
            LEFT JOIN cameras c ON c.id = l.cam_id
            WHERE 1 = 1
        """
        params = []

        if start_dt:
            query += " AND l.datetimeStart >= ?"
            params.append(start_dt)
        if end_dt:
            query += " AND l.datetimeStart <= ?"
            params.append(end_dt)
        if camera_id:
            query += " AND l.cam_id = ?"
            params.append(camera_id)
        if event_type:
            query += " AND l.event_type = ?"
            params.append(event_type)

        query += " ORDER BY l.datetimeStart DESC"

        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)

        self.cur.execute(query, tuple(params))
        return self.cur.fetchall()

    def fetch_event_types_for_dashboard(self):
        self.cur.execute("""
            SELECT name FROM classes
            UNION
            SELECT event_type
            FROM logs
            WHERE event_type IS NOT NULL AND event_type <> ''
            ORDER BY 1
        """)
        return [row[0] for row in self.cur.fetchall()]

    def fetch_class_danger_levels(self):
        self.cur.execute("""
            SELECT name, danger_level
            FROM classes
        """)
        return {name: danger_level for name, danger_level in self.cur.fetchall()}

    def fetch_dashboard_snapshot(self, start_dt=None, end_dt=None, camera_id=None, event_type=None):
        events = self.fetch_dashboard_events(
            start_dt=start_dt,
            end_dt=end_dt,
            camera_id=camera_id,
            event_type=event_type,
            limit=None,
        )

        by_type = {}
        by_camera = {}
        durations = []
        active_events = 0

        for _, cam_id, camera_name, location, dt_start, dt_stop, etype, _, _ in events:
            etype = etype or "unknown"
            camera_label = camera_name or f"Camera {cam_id}"
            if location:
                camera_label = f"{camera_label} ({location})"

            by_type[etype] = by_type.get(etype, 0) + 1
            by_camera[camera_label] = by_camera.get(camera_label, 0) + 1

            if not dt_stop:
                active_events += 1
                continue

            start = self._parse_log_datetime(dt_start)
            stop = self._parse_log_datetime(dt_stop)
            if start is not None and stop is not None:
                duration = max(0.0, (stop - start).total_seconds())
                durations.append(duration)

        avg_duration = sum(durations) / len(durations) if durations else 0.0

        return {
            "events": events,
            "total": len(events),
            "active": active_events,
            "finished": len(events) - active_events,
            "avg_duration": avg_duration,
            "by_type": by_type,
            "by_camera": by_camera,
        }

    @staticmethod
    def _parse_log_datetime(value):
        if not value:
            return None

        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None
