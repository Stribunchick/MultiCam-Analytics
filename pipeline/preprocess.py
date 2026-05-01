import multiprocessing
import queue
import torch
import cv2
import numpy as np
import time

from pipeline.runtime_metrics import PREPROCESS_KEY, now_iso
# from datetime import datetime
class PreprocessWorker(multiprocessing.Process):
    def __init__(self, frame_queues, tensor_queue, batch_size, metrics_state=None):
        super().__init__()
        self.frame_queues = frame_queues
        self.tensor_queue = tensor_queue
        self.batch_size = batch_size
        self.metrics_state = metrics_state
        
        self.model_img_size = (416, 416)
        self.stop_evt = multiprocessing.Event()
        print("PREPROCESS INIT")

    def run(self):
        batches_total = 0
        frames_total = 0
        queue_overwrites = 0
        frames_since_report = 0
        batch_size_sum = 0
        batch_ms_sum = 0.0
        last_report_at = time.monotonic()

        while not self.stop_evt.is_set():
            batch_started_at = time.perf_counter()
            tensors = []
            FCs = []
            
            for fq in self.frame_queues.values():
                try:
                    frame = fq.get(timeout=0.1)# get the frame
                except queue.Empty:
                    continue
                # print("start preprocess", datetime.now())
                # start = datetime.now()
                tensor = self.preprocess(frame.image) # Convert from image to tensor
                tensors.append(tensor)
                FCs.append(frame)   # Form a packet where each tensor is corresponding to the frame
            if tensors: # Send to inference
                batch = torch.stack(tensors).pin_memory()
                # stop = datetime.now()
                # print(f"[PrePW] START FROM BATCH: {start}, SEND: {stop}")
                # print([f"[ppw] {batch}"])
                packet = {
                    "tensors": batch,
                    "FCs": FCs
                }
                if self._put_latest_packet(packet):
                    queue_overwrites += 1

                batch_size = len(FCs)
                batch_ms = (time.perf_counter() - batch_started_at) * 1000.0
                batches_total += 1
                frames_total += batch_size
                frames_since_report += batch_size
                batch_size_sum += batch_size
                batch_ms_sum += batch_ms

                if time.monotonic() - last_report_at >= 1.0:
                    report_interval = max(time.monotonic() - last_report_at, 1e-6)
                    self._publish_metrics(
                        batches_total,
                        frames_total,
                        batch_size,
                        batch_size_sum / max(batches_total, 1),
                        batch_ms,
                        batch_ms_sum / max(batches_total, 1),
                        frames_since_report / report_interval,
                        queue_overwrites,
                    )
                    frames_since_report = 0
                    last_report_at = time.monotonic()

## Оптимизировать то, что снизу
    def preprocess(self, frame):
        # resize
        img = frame
        frame = cv2.resize(img, self.model_img_size)

        # BGR → RGB
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # HWC → CHW
        frame_chw = np.ascontiguousarray(frame.transpose(2, 0, 1))

        # uint8 → float32 [0..1]
        tensor = torch.from_numpy(frame_chw).float().div_(255.0).half()

        return tensor

    def _publish_metrics(
        self,
        batches_total,
        frames_total,
        last_batch_size,
        avg_batch_size,
        last_batch_ms,
        avg_batch_ms,
        fps,
        queue_overwrites,
    ):
        if self.metrics_state is None:
            return

        self.metrics_state[PREPROCESS_KEY] = {
            "batches_total": batches_total,
            "frames_total": frames_total,
            "last_batch_size": last_batch_size,
            "avg_batch_size": round(avg_batch_size, 2),
            "last_batch_ms": round(last_batch_ms, 2),
            "avg_batch_ms": round(avg_batch_ms, 2),
            "fps": round(fps, 2),
            "queue_overwrites": queue_overwrites,
            "updated_at": now_iso(),
        }

    def _put_latest_packet(self, packet):
        try:
            self.tensor_queue.put_nowait(packet)
            return False
        except queue.Full:
            pass

        try:
            self.tensor_queue.get_nowait()
        except queue.Empty:
            pass

        try:
            self.tensor_queue.put_nowait(packet)
        except queue.Full:
            pass

        return True
    
    def stop(self):
        self.stop_evt.set()
