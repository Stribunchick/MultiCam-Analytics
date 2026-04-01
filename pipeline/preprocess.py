import multiprocessing
import queue
import torch
import cv2
import numpy as np
import time
# from datetime import datetime
class PreprocessWorker(multiprocessing.Process):
    def __init__(self, frame_queues, tensor_queue, batch_size):
        super().__init__()
        self.frame_queues = frame_queues
        self.tensor_queue = tensor_queue
        self.batch_size = batch_size
        
        self.model_img_size = (416, 416)
        self.stop_evt = multiprocessing.Event()
        print("PREPROCESS INIT")

    def run(self):
        while not self.stop_evt.is_set():
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
                try:
                    self.tensor_queue.put({
                        "tensors": batch,
                        "FCs": FCs
                    })
                except queue.Full:
                    self.tensor_queue.get_nowait()
                    # time.sleep(0.5)
                    self.tensor_queue.put_nowait({
                        "tensors": batch,
                        "FCs": FCs
                    })
                # print("stop preprocess", datetime.now())

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
    
    def stop(self):
        self.stop_evt.set()