import os
from operator import mul

from ultralytics import YOLO
import queue
import sys
import multiprocessing
import torch
import json

from pipeline.cameraCapture import CameraCapture
from pipeline.preprocess import PreprocessWorker
from pipeline.inferenceWorker import InferenceWorker
from pipeline.postprocess import PostProcessWorker
from pipeline.render import VideoWall
from pipeline.dblogger import DBLogger
from pipeline.runtime_metrics import init_metrics_state, mark_session_status
from gui.dashboardWindow import DashboardWindow
from gui.db_worker import DBWorker

# Получить кадр с камеры
# Передать кадры на инференс
# В будущем сделать редактор реакции на событие.

# BATCH_SIZE = 8
# IMG_SIZE_TEST = (640, 480)
# DEVICE = "cuda:0"
# CONF_THRESH = 0.7
# DB_PATH = "./db/logs.db"


class VideoWallExec:
    def __init__(self, cameras, models, config, DB_PATH, CLASSES, DEVICE="cuda:0", BATCH_SIZE=2):
        self.cameras = cameras
        self.models = models
        self.BATCH_SIZE = BATCH_SIZE
        self.config = config
        self.DB_PATH = DB_PATH
        self.DEVICE = DEVICE
        self.CLASSES = CLASSES
        self.wall = None
        self.dashboard_window = None
        self.config_id, self.config_name, self.cameras_per_row, self.enabled, self.CONF_THRESH, self.fps = config
        self.dbworker = DBWorker(DB_PATH)
        
        # cameras = [{"id":..., "ip":..., ...}]
        self.cam_ids = [camera["id"] for camera in cameras]
        self.cam_workers = {}
        self.maxqsize = 2
        self.snapshot_dir = os.path.abspath(
            os.path.join(".", "db", "snapshots", f"config_{self.config_id}")
        )

    def start_videowall(self):
        print("STARTING THE VIDEOWALL...")
        cameras = self.cameras
        models = self.models
        saved_rois = self.dbworker.fetch_rois_by_config_id(self.config_id)

        self.roi_manager = multiprocessing.Manager()
        self.roi_state = self.roi_manager.dict({
            cam_id: saved_rois.get(cam_id)
            for cam_id in self.cam_ids
        })
        self.metrics_state = self.roi_manager.dict()
        init_metrics_state(
            self.metrics_state,
            self.cameras,
            models,
            self.fps,
            self.BATCH_SIZE,
        )
        mark_session_status(self.metrics_state, "running")

        #frames_queue = multiprocessing.Queue(maxsize=128)
        self.fqs = {}
        for camera in self.cameras:
            path = self.form_rtsp_link(camera["username"], camera["pwd"], camera["ip"])
            frames_queue = multiprocessing.Queue(self.maxqsize)
            cc = CameraCapture(
                path,
                frames_queue,
                camera["id"],
                fps=self.fps,
                metrics_state=self.metrics_state,
            )
            self.cam_workers[camera["id"]] = cc
            self.fqs[camera["id"]] = frames_queue

        tensor_queue = multiprocessing.Queue(self.maxqsize)
        prepw = PreprocessWorker(
            self.fqs,
            tensor_queue,
            self.BATCH_SIZE,
            metrics_state=self.metrics_state,
        )

        result_queue = torch.multiprocessing.Queue(self.maxqsize)
        inf_w = InferenceWorker(
            tensor_queue,
            result_queue,
            models,
            device=self.DEVICE,
            conf_thresh=self.CONF_THRESH,
            metrics_state=self.metrics_state,
        )

        out_queues = {cam_id: multiprocessing.Queue(self.maxqsize) for cam_id in self.cam_ids}
        log_queue_task = multiprocessing.Queue()
        postpw = PostProcessWorker(
            result_queue,
            out_queues,
            log_queue_task,
            self.cam_ids,
            self.CONF_THRESH,
            allowed_classes=self.CLASSES,
            roi_state=self.roi_state,
            metrics_state=self.metrics_state,
            snapshot_dir=self.snapshot_dir,
        )
        
        dblogger = DBLogger(self.DB_PATH, log_queue_task)
        dblogger.init_logs()
        
        self.wall = VideoWall(
            out_queues,
            self.cam_ids,
            self.roi_state,
            cameras_per_row=self.cameras_per_row,
            fps=self.fps,
            metrics_state=self.metrics_state,
            camera_names={camera["id"]: camera["name"] for camera in self.cameras},
        )
        self.wall.roi_changed.connect(self._save_roi)
        self.wall.analytics_requested.connect(self._open_dashboard)
        self.wall.resize(1280, 480)
        
        self.wall.show()
        
        for cc in self.cam_workers.values():
            cc.start()

        prepw.start()
        inf_w.start()
       
        postpw.start()
        dblogger.start()
        
        def stop_threads():
            print("Stopping the videowall...")
            mark_session_status(self.metrics_state, "stopping")
            for cc in self.cam_workers.values():
                cc.stop()
                cc.join()
                # if cc.is_alive():
                #     cc.terminate()
            prepw.stop()
            prepw.join(timeout=1)
            if prepw.is_alive():
                prepw.terminate()
            inf_w.stop()
            inf_w.join(timeout=1)
            if inf_w.is_alive():
                inf_w.terminate()
            postpw.stop()
            postpw.join(timeout=1)
            if postpw.is_alive():
                postpw.terminate()
            dblogger.stop()
            dblogger.join()
            if dblogger.is_alive():
                dblogger.terminate()
            mark_session_status(self.metrics_state, "stopped")
            self.roi_manager.shutdown()
            print("Videowall stopped")
        self.wall.destroyed.connect(stop_threads)

    def _save_roi(self, cam_id, roi):
        self.dbworker.save_roi(self.config_id, cam_id, roi)

    def _open_dashboard(self):
        if self.dashboard_window is not None and self.dashboard_window.isVisible():
            self.dashboard_window.refresh()
            self.dashboard_window.raise_()
            self.dashboard_window.activateWindow()
            return

        self.dashboard_window = DashboardWindow(self.dbworker)
        self.dashboard_window.destroyed.connect(self._on_dashboard_closed)
        self.dashboard_window.show()

    def _on_dashboard_closed(self):
        self.dashboard_window = None
        
    def form_rtsp_link(self, username, pwd, ip):
        link = f'rtsp://{username}:{pwd}@{ip}:554/Streaming/101'
        return link


if __name__ == "__main__":
    multiprocessing.set_start_method("spawn")
