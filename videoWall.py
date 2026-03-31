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
        _, self.config_name, self.cameras_per_row, self.enabled, self.CONF_THRESH, self.fps = config
        
        # cameras = [{"id":..., "ip":..., ...}]
        self.cam_ids = [camera["id"] for camera in cameras]
        self.cam_workers = {}
    def start_videowall(self):
        print("STARTING THE VIDEOWALL...")
        cameras = self.cameras
        
        models = self.models
        
        frames_queue = multiprocessing.Queue(maxsize=128)
        for camera in self.cameras:
            path = self.form_rtsp_link(camera["username"], camera["pwd"], camera["ip"])
            cc = CameraCapture(path, frames_queue, camera["id"])
            self.cam_workers[camera["id"]] = cc

        tensor_queue = multiprocessing.Queue(maxsize=64)
        prepw = PreprocessWorker(frames_queue, tensor_queue, self.BATCH_SIZE)

        result_queue = torch.multiprocessing.Queue(maxsize=64)
        inf_w = InferenceWorker(tensor_queue, result_queue, models, device=self.DEVICE, conf_thresh = self.CONF_THRESH)

        out_queues = {cam_id: multiprocessing.Queue(maxsize=64) for cam_id in self.cam_ids}
        log_queue_task = multiprocessing.Queue()
        postpw = PostProcessWorker(result_queue, out_queues, log_queue_task, self.cam_ids, self.CONF_THRESH, allowed_classes=self.CLASSES)
        
        dblogger = DBLogger(self.DB_PATH, log_queue_task)
        dblogger.init_logs()
        
        self.wall = VideoWall(out_queues, self.cam_ids, cameras_per_row=self.cameras_per_row, fps=self.fps)
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
            for cc in self.cam_workers.values():
                cc.stop()
                cc.join()
                if cc.is_alive():
                    cc.terminate()
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
            print("Videowall stopped")
        self.wall.destroyed.connect(stop_threads)
        
    def form_rtsp_link(self, username, pwd, ip):
        link = f'rtsp://{username}:{pwd}@{ip}:554/Streaming/101'
        return link


if __name__ == "__main__":
    multiprocessing.set_start_method("spawn")