import sqlite3
# from UI_python.tools.config import Config

import os
import sys

from PySide6.QtCore import QSize
from PySide6.QtWidgets import QApplication, QMainWindow, QTableView

class DBWorker:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)
        self.cur = self.conn.cursor()
        self.init_tables()
        

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
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.commit()

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

        self.cur.execute("""
                DELETE FROM configs WHERE id = ?
        """, (config_id,))
        self.conn.commit()

    def delete_camera(self, camera_id):

        """
        Удалить камеру и все связи CASCADE?
        """
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
            SELECT c.*
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
        return
    
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
            SELECT id, name, model_id FROM classes
        """)
        return self.cur.fetchall()

    def add_model(self, model_path):
        self.cur.execute("""
            INSERT INTO models (model_path) VALUES (?)
        """, (model_path,))
        self.conn.commit()
        model_id = self.cur.lastrowid
        return model_id
    
    def add_class(self, name, model_id):
        self.cur.execute("""
            INSERT INTO classes (name, model_id) VALUES (?, ?)
        """, (name, model_id, ))
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
        for _, _, model_id in classes:
            models_ids.add(model_id)
        models_ids = list(models_ids)
        placeholders = ",".join("?" for _ in models_ids)
        query = f"SELECT id, model_path FROM models WHERE id IN ({placeholders})"
        self.cur.execute(query, tuple(models_ids))
        return self.cur.fetchall()