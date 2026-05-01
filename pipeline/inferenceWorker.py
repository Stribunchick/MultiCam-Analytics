import torch
import multiprocessing
import queue
import time
from ultralytics.utils import nms

from pipeline.runtime_metrics import INFERENCE_KEY, now_iso
# from datetime import datetime

class InferenceWorker(torch.multiprocessing.Process):
    def __init__(self, tensors_queue, result_queue, models, device, conf_thresh, metrics_state=None):
        super().__init__()

        self.tensors_queue = tensors_queue
        self.result_queue = result_queue
        self.stop_evt = multiprocessing.Event()
        self.conf_thresh = conf_thresh
        self.device = device
        self.models = models
        self.metrics_state = metrics_state
        self.names = []
        
        #self.streams = [torch.cuda.Stream() for _ in self.models]
        
        print("INFERENCE WORKER INIT")

    def run(self):
        torch.cuda.set_device(self.device)
        self.models, self.names = self.load_models(self.models)
        batches_total = 0
        frames_total = 0
        dropped_results = 0
        frames_since_report = 0
        inference_ms_sum = 0.0
        device_ref = torch.device(self.device)
        last_report_at = time.monotonic()

        while not self.stop_evt.is_set():
            try:
                packet = self.tensors_queue.get() # Acquire FrameClasses and corresponding tensors
            except:
                continue
            # print("start inference", datetime.now())
            # start = datetime.now()
            # print([f"[IW] {packet["tensors"]}"])
            batch = packet["tensors"].to(self.device, non_blocking=True).half()
            FCs = packet["FCs"]
            inference_started_at = time.perf_counter()
            
            all_results = []
            names = []
            with torch.no_grad():
                for i, model in enumerate(self.models):
                    preds = model(batch)
                    preds = nms.non_max_suppression(
                        preds,
                        conf_thres=self.conf_thresh,
                        iou_thres=0.45,
                        max_det=100,
                    )
                    preds = [x.cpu() for x in preds]
                    all_results.append(preds)
                    names.append(self.names[i])
            
            inference_ms = (time.perf_counter() - inference_started_at) * 1000.0
            del batch
            # torch.cuda.empty_cache()
            # print(all_results)
            # stop = datetime.now()
            # print(f"[IW] START INFERENCE BATCH: {start}, STOP: {stop}")
            try:
                packet = {
                    "results": all_results,
                    "FCs": FCs,
                    "names": names
                }
                self.result_queue.put_nowait(packet)
                # print("stop batch inference", datetime.now())
            except queue.Full:
                dropped_results += 1

            batch_size = len(FCs)
            batches_total += 1
            frames_total += batch_size
            frames_since_report += batch_size
            inference_ms_sum += inference_ms

            if time.monotonic() - last_report_at >= 1.0:
                report_interval = max(time.monotonic() - last_report_at, 1e-6)
                self._publish_metrics(
                    batches_total,
                    frames_total,
                    batch_size,
                    inference_ms,
                    inference_ms_sum / max(batches_total, 1),
                    frames_since_report / report_interval,
                    dropped_results,
                    torch.cuda.memory_allocated(device_ref) / (1024 ** 2),
                    torch.cuda.memory_reserved(device_ref) / (1024 ** 2),
                    torch.cuda.max_memory_allocated(device_ref) / (1024 ** 2),
                )
                frames_since_report = 0
                last_report_at = time.monotonic()

    def load_yolo(self, model, device ="cuda:0"):
        from ultralytics import YOLO
        yolo = YOLO(model)
        net = yolo.model
        classes = self._normalize_names(yolo.names)
        net.fuse()
        net.to(device)
        net.eval()
        net.half()
        return (net, classes)

    def _normalize_names(self, classes):
        if isinstance(classes, dict):
            normalized = {}
            for key, value in classes.items():
                try:
                    normalized[int(key)] = str(value)
                except (TypeError, ValueError):
                    continue
            return normalized

        if isinstance(classes, (list, tuple)):
            return {
                idx: str(value)
                for idx, value in enumerate(classes)
            }

        return {}

    def load_models(self, models):
        ms = []
        mcls = {}
        print(models)
        for i, model in enumerate(models):
            _, mp = model
            mp = "./weights/" + mp
            
            m, classes = self.load_yolo(mp)
            ms.append(m)
            mcls[i] = classes
        return ms, mcls

    def _publish_metrics(
        self,
        batches_total,
        frames_total,
        last_batch_size,
        last_inference_ms,
        avg_inference_ms,
        fps,
        queue_drops,
        gpu_allocated_mb,
        gpu_reserved_mb,
        gpu_peak_mb,
    ):
        if self.metrics_state is None:
            return

        self.metrics_state[INFERENCE_KEY] = {
            "batches_total": batches_total,
            "frames_total": frames_total,
            "last_batch_size": last_batch_size,
            "last_inference_ms": round(last_inference_ms, 2),
            "avg_inference_ms": round(avg_inference_ms, 2),
            "fps": round(fps, 2),
            "queue_drops": queue_drops,
            "gpu_allocated_mb": round(gpu_allocated_mb, 2),
            "gpu_reserved_mb": round(gpu_reserved_mb, 2),
            "gpu_peak_mb": round(gpu_peak_mb, 2),
            "updated_at": now_iso(),
        }

    def stop(self):
        self.stop_evt.set()


                
