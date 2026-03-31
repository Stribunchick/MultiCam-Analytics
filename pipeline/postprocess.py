import multiprocessing
import queue
import cv2
import uuid
from deep_sort_realtime.deepsort_tracker import DeepSort
from pipeline.frameClass import Frame
from datetime import datetime
class PostProcessWorker(multiprocessing.Process):
    def __init__(self, to_process_queue, out_queues, log_task_queue, cam_ids, conf_thresh=0.6, img_size=(640, 480), img_size_resized=(416, 416), allowed_classes:list[str] =[]):
        super().__init__()
        self.stop_evt = multiprocessing.Event()
        self.to_process_queue = to_process_queue
        self.out_queues = out_queues 
        self.conf_thresh = conf_thresh
        self.log_task_queue = log_task_queue
        
        self.cam_ids = cam_ids
        self.img_size = img_size
        self.img_size_resized=  img_size_resized
        x, y = self.img_size
        x1, y1 = self.img_size_resized
        self.sx = x / x1
        self.sy = y / y1
        
        self.active_tracks = {cam_id: {} for cam_id in cam_ids}
        if len(allowed_classes) != 0:
            self.allowed_classes = [x for _, x, _ in allowed_classes]
        else:
            self.allowed_classes = None

        print("POSTPROCESS INIT")


    def run(self):
        self.trackers = {cam_id: DeepSort(nn_budget=15,max_iou_distance=0.8, max_age=30, n_init=3, embedder="mobilenet", half=True, embedder_gpu=True) for cam_id in self.cam_ids}
        
        while not self.stop_evt.is_set():
            # Decode boxes(scale back),Draw, track, send to pyqt
            
                # packet = self.to_process_queue.get(timeout=0.01)
            packet = self.to_process_queue.get()
            
            
            results = packet["results"]
            # print(results)
            frames: list[Frame] = packet["FCs"]
            names = packet["names"]
            # start = datetime.now()
            #Каждый кадр из батча
            for i in range(len(frames)):
                detections = []
                cam_id = frames[i].cam_id
                timestamp = frames[i].timestamp
                # Результат каждой модели для i-го кадра
                for m in range(len(results)):

                    res = results[m][i]
                    resnames = names[m]
                    res = res.numpy()
                
                    boxes = res[:, :4]
                    confs = res[:, 4]
                    clss = res[:, 5]
                    for box, conf, cls in zip(boxes, confs, clss):
                        cls_name = resnames[int(cls)]#classes_names[int(cls)]
                        x1, y1, x2, y2 = map(int, box)
                        x1 = int(x1*self.sx)
                        y1 = int(y1*self.sy)
                        x2 = int(x2*self.sx)
                        y2 = int(y2*self.sy)

                        w = x2-x1
                        h = y2-y1

                        detections.append([[x1, y1, w, h], float(conf), cls_name])
            # Track here                
                tracks = self.trackers[cam_id].update_tracks(detections, frame=frames[i].image)
            # Send the task here check if the track is in active tracks.
            # If one of active_tracks not in tracks -> make log
            # If active_track in tracks -> pass
            # If tracK not in active_tracks -> end log

            #-- логирование здесь

                cam_active = self.active_tracks[cam_id]
                
                current_active = set()
                
                for track in tracks:
                    
                    if not track.is_confirmed():
                        continue
                    if track.det_class not in self.allowed_classes:
                        continue
                    
                    track_id = track.track_id
                    current_active.add(track_id)

                    if not track_id in cam_active :
                        log_id = timestamp + str(track_id)
                        # print(log_id)
                        cam_active[track_id] = {
                            "log_id": log_id,
                            "start_time": timestamp,
                            "class_name": track.det_class                        
                            }
                        
                        self.log_task_queue.put_nowait({
                            "action": "start",
                            "id": log_id,
                            "datetimeStart": cam_active[track_id]["start_time"],
                            "cam_id": cam_id,
                            "event_type": track.det_class,
                            "src": "test"
                        })
                    else:
                        continue
                    
                lost_ids = set(cam_active.keys()) - current_active

                for track_id in lost_ids:
                    log_info = cam_active[track_id]
                    self.log_task_queue.put_nowait({
                        "action": "end",
                        "log_id": log_info["log_id"],
                        "datetimeStop": timestamp,
                    }) 
                
                    del cam_active[track_id]

                

                self.draw_tracks(frames[i].image, tracks)
                # stop = datetime.now()
                # print(f"[PostPW] START BATCH: {start}, POST FRAME {stop}")
                try:
                    self.out_queues[cam_id].put_nowait(
                    {"frame": frames[i]}
                    )
                    # print("stop postprocess", datetime.now())
                except queue.Full:
                    pass


    def draw_tracks(self, frame, tracks):    
        for track in tracks:
            if not track.is_confirmed():
                continue
            #print(track)
            x1, y1, x2, y2 = map(int, track.to_ltrb())
            track_id = track.track_id
            cls_name = track.det_class
            color = (0, 255, 0)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

            label = f"{cls_name} ID:{track_id}"
            cv2.putText(
                frame,
                label,
                (x1, y1-5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                1
            )

    def stop(self):
        self.stop_evt.set()