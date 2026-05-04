import os
from operator import mul
import threading
import traceback

from ultralytics import YOLO
import queue
import sys
import multiprocessing
import torch
import json
from PySide6.QtCore import QTimer

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
    def __init__(self, cameras, models, config, DB_PATH, CLASSES, DEVICE="cuda:0", BATCH_SIZE=2, main_window=None):
        self.cameras = cameras
        self.models = models
        self.BATCH_SIZE = BATCH_SIZE
        self.config = config
        self.DB_PATH = DB_PATH
        self.DEVICE = DEVICE
        self.CLASSES = CLASSES
        self.main_window = main_window
        self.wall = None
        self.dashboard_window = None
        self.dashboard_window_token = None
        self._stopping = False
        self._show_main_after_shutdown = False
        self._stop_thread = None
        self._stopped_evt = threading.Event()
        self._stopped_evt.set()
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
        self._stopped_evt.clear()
        cameras = self.cameras
        models = self.models
        saved_rois = self.dbworker.fetch_rois_by_config_id(self.config_id)
        processing_enabled = bool(self.enabled)

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

        prepw = None
        inf_w = None
        postpw = None
        dblogger = None
        tensor_queue = None
        result_queue = None
        log_queue_task = None
        alert_queue = None
        alert_decisions = None

        if processing_enabled:
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
            alert_queue = multiprocessing.Queue()
            alert_decisions = self.roi_manager.dict()
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
                alert_queue=alert_queue,
                alert_decisions=alert_decisions,
            )

            dblogger = DBLogger(self.DB_PATH, log_queue_task)
            dblogger.init_logs()
        else:
            out_queues = self.fqs
        
        self.wall = VideoWall(
            out_queues,
            self.cam_ids,
            self.roi_state,
            cameras_per_row=self.cameras_per_row,
            fps=self.fps,
            metrics_state=self.metrics_state,
            camera_names={
                camera["id"]: self._format_camera_title(camera)
                for camera in self.cameras
            },
            alert_queue=alert_queue,
            alert_decisions=alert_decisions,
            class_danger_levels={
                cls[1]: cls[3]
                for cls in self.CLASSES
                if len(cls) > 3
            },
        )
        self.wall.roi_changed.connect(self._save_roi)
        self.wall.analytics_requested.connect(self._open_dashboard)
        self.wall.main_window_requested.connect(self._return_to_main_window)
        self.wall.resize(*self.wall.recommended_size())
        
        self.wall.show()
        
        for cc in self.cam_workers.values():
            cc.start()

        if prepw is not None:
            prepw.start()
        if inf_w is not None:
            inf_w.start()
        if postpw is not None:
            postpw.start()
        if dblogger is not None:
            dblogger.start()
        
        def shutdown_pipeline():
            print("Stopping the videowall...")
            try:
                mark_session_status(self.metrics_state, "stopping")
                for cc in self.cam_workers.values():
                    cc.stop()
                for cc in self.cam_workers.values():
                    cc.join(timeout=3.0)

                if prepw is not None:
                    prepw.stop()
                    prepw.join(timeout=1)
                    if prepw.is_alive():
                        prepw.terminate()
                        prepw.join(timeout=1)
                if inf_w is not None:
                    inf_w.stop()
                    inf_w.join(timeout=1)
                    if inf_w.is_alive():
                        inf_w.terminate()
                        inf_w.join(timeout=1)
                if postpw is not None:
                    postpw.stop()
                    postpw.join(timeout=1)
                    if postpw.is_alive():
                        postpw.terminate()
                        postpw.join(timeout=1)
                if dblogger is not None:
                    dblogger.stop()
                    dblogger.join(timeout=1)
                    if dblogger.is_alive():
                        dblogger.terminate()
                        dblogger.join(timeout=1)

                for fq in self.fqs.values():
                    try:
                        fq.close()
                        fq.join_thread()
                    except Exception:
                        pass
                if processing_enabled:
                    for oq in out_queues.values():
                        try:
                            oq.close()
                            oq.join_thread()
                        except Exception:
                            pass
                    for q in (tensor_queue, result_queue, log_queue_task, alert_queue):
                        if q is None:
                            continue
                        try:
                            q.close()
                            q.join_thread()
                        except Exception:
                            pass

                mark_session_status(self.metrics_state, "stopped")
            except Exception:
                traceback.print_exc()
            finally:
                try:
                    self.roi_manager.shutdown()
                except Exception:
                    pass
                self.wall = None
                self._stopping = False
                self._stopped_evt.set()
                print("Videowall stopped")

        def stop_threads():
            if self._stopping:
                return

            self._stopping = True
            if self.dashboard_window is not None:
                try:
                    self.dashboard_window.close()
                except RuntimeError:
                    pass
                self.dashboard_window = None
                self.dashboard_window_token = None
            if (
                not self._show_main_after_shutdown
                and self.main_window is not None
                and not getattr(self.main_window, "_pending_app_exit", False)
            ):
                self._show_main_after_shutdown = True
            if self._show_main_after_shutdown and self.main_window is not None:
                request_return = getattr(self.main_window, "request_return_from_videowall", None)
                if callable(request_return):
                    request_return()
            self._stop_thread = threading.Thread(target=shutdown_pipeline, daemon=True)
            self._stop_thread.start()
        self.wall.closing.connect(stop_threads)

    def _save_roi(self, cam_id, roi):
        self.dbworker.save_roi(self.config_id, cam_id, roi)

    def _format_camera_title(self, camera):
        name = (camera.get("name") or "").strip()
        location = (camera.get("location") or "").strip()

        if name and location:
            return f"{name} - {location}"
        if name:
            return name
        if location:
            return location
        return f"Камера {camera['id']}"

    def _open_dashboard(self):
        if self.dashboard_window is not None:
            try:
                if self.dashboard_window.isVisible():
                    self.dashboard_window.refresh()
                    self.dashboard_window.raise_()
                    self.dashboard_window.activateWindow()
                    return
            except RuntimeError:
                self.dashboard_window = None
                self.dashboard_window_token = None

        window_token = object()
        window = DashboardWindow(self.dbworker)
        window.destroyed.connect(
            lambda *_args, token=window_token: self._on_dashboard_closed(token)
        )
        window.show()

        self.dashboard_window = window
        self.dashboard_window_token = window_token

    def _on_dashboard_closed(self, token=None):
        if token is None or token is self.dashboard_window_token:
            self.dashboard_window = None
            self.dashboard_window_token = None

    def _return_to_main_window(self):
        if self.wall is None or self._stopping:
            return

        self._show_main_after_shutdown = True
        self.wall.hide()
        QTimer.singleShot(0, self.wall.close)

    def request_shutdown(self):
        if self._stopped_evt.is_set():
            return

        if self.wall is not None and not self._stopping:
            self._show_main_after_shutdown = False
            self.wall.hide()
            QTimer.singleShot(0, self.wall.close)

    def is_shutdown_complete(self):
        return self._stopped_evt.is_set()

    def _show_main_window(self):
        if self.main_window is None:
            return

        try:
            prepare_return = getattr(self.main_window, "prepare_return_from_videowall", None)
            if callable(prepare_return):
                prepare_return()
            else:
                self.main_window.showNormal()
                self.main_window.show()
                self.main_window.raise_()
                self.main_window.activateWindow()
        except RuntimeError:
            self.main_window = None
        
    def form_rtsp_link(self, username, pwd, ip):
        link = f'rtsp://{username}:{pwd}@{ip}:554/Streaming/101'
        return link


if __name__ == "__main__":
    multiprocessing.set_start_method("spawn")
