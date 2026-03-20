import sqlite3
# from UI_python.tools.config import Config

import os
import sys

from PySide6.QtCore import QSize
from PySide6.QtSql import (
    QSqlDatabase,
    QSqlRelation,
    QSqlRelationalTableModel,
)
from PySide6.QtWidgets import QApplication, QMainWindow, QTableView

class DBWorker:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)
        self.cur = self.conn.cursor()
        self.init_tables()
        self.db = QSqlDatabase("QSQLITE")
        self.db.setDatabaseName(db_path)
        self.db.open()

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
                                index_in_model INTEGER,
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

    def delete_config(self, config_id):

        """
        Удалить конфиг и все связи CASCADE?
        """

        self.cur.execute("""
                DELETE FROM configs WHERE id = ?
        """, (config_id,))
        self.conn.commit()
        