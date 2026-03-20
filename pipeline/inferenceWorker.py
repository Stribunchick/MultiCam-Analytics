import torch
import multiprocessing
import queue
from ultralytics.utils import nms
# from datetime import datetime
# from datetime import datetime
class InferenceWorker(torch.multiprocessing.Process):
    def __init__(self, tensors_queue,result_queue, models, device, conf_thresh):
        super().__init__()

        self.tensors_queue = tensors_queue
        self.result_queue = result_queue
        self.stop_evt = multiprocessing.Event()
        self.conf_thresh = conf_thresh
        self.device = device
        self.models = models
        self.names = []
        
        #self.streams = [torch.cuda.Stream() for _ in self.models]
        
        print("INFERENCE WORKER INIT")

    def run(self):
        torch.cuda.set_device(self.device)
        self.models, self.names = self.load_models(self.models)
        while not self.stop_evt.is_set():
            try:
                packet = self.tensors_queue.get_nowait() # Acquire FrameClasses and corresponding tensors
            except queue.Empty:
                continue
            # print("start inference", datetime.now())
            # start = datetime.now()
            # print([f"[IW] {packet["tensors"]}"])
            batch = packet["tensors"].to(self.device, non_blocking=True).half()
            FCs = packet["FCs"]
            
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
                pass
    def load_yolo(self, model, device ="cuda:0"):
        from ultralytics import YOLO
        yolo = YOLO(model)
        net = yolo.model
        classes = yolo.names
        net.fuse()
        net.to(device)
        net.eval()
        net.half()
        return (net, classes)

    def load_models(self, models):
        ms = []
        mcls = {}
        print(models)
        for i, model in enumerate(models):
            _, mp = model
            mp = "./weights/" + model
            
            m, classes = self.load_yolo(mp)
            ms.append(m)
            mcls[i] = classes
        return ms, mcls
    def stop(self):
        self.stop_evt.set()


                