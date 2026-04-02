import multiprocessing
import queue
import cv2

from deep_sort_realtime.deepsort_tracker import DeepSort
from pipeline.frameClass import Frame


class PostProcessWorker(multiprocessing.Process):
    def __init__(
        self,
        to_process_queue,
        out_queues,
        log_task_queue,
        cam_ids,
        conf_thresh=0.6,
        img_size_resized=(416, 416),
        allowed_classes: list[str] = None,
        counters_enabled=True,
        roi_state=None,
    ):
        super().__init__()
        self.stop_evt = multiprocessing.Event()
        self.to_process_queue = to_process_queue
        self.out_queues = out_queues
        self.conf_thresh = conf_thresh
        self.log_task_queue = log_task_queue
        self.cam_ids = cam_ids
        self.model_img_size = img_size_resized
        self.roi_state = roi_state

        self.active_tracks = {cam_id: {} for cam_id in cam_ids}
        if allowed_classes:
            self.allowed_classes = [name for _, name, _ in allowed_classes]
        else:
            self.allowed_classes = None

        self.counters_enabled = counters_enabled
        print("POSTPROCESS INIT")

    def run(self):
        self.trackers = {
            cam_id: DeepSort(
                nn_budget=15,
                max_iou_distance=0.8,
                max_age=30,
                n_init=3,
                embedder="mobilenet",
                half=True,
                embedder_gpu=True,
            )
            for cam_id in self.cam_ids
        }

        while not self.stop_evt.is_set():
            packet = self.to_process_queue.get()

            results = packet["results"]
            frames: list[Frame] = packet["FCs"]
            names = packet["names"]

            for frame_idx, frame in enumerate(frames):
                detections = []
                cam_id = frame.cam_id
                timestamp = frame.timestamp
                frame_h, frame_w = frame.image.shape[:2]
                sx = frame_w / self.model_img_size[0]
                sy = frame_h / self.model_img_size[1]

                for model_idx, model_results in enumerate(results):
                    res = model_results[frame_idx].numpy()
                    resnames = names[model_idx]

                    boxes = res[:, :4]
                    confs = res[:, 4]
                    clss = res[:, 5]
                    for box, conf, cls in zip(boxes, confs, clss):
                        cls_name = resnames[int(cls)]
                        x1, y1, x2, y2 = map(int, box)
                        x1 = int(x1 * sx)
                        y1 = int(y1 * sy)
                        x2 = int(x2 * sx)
                        y2 = int(y2 * sy)

                        w = x2 - x1
                        h = y2 - y1
                        detections.append([[x1, y1, w, h], float(conf), cls_name])

                tracks = self.trackers[cam_id].update_tracks(detections, frame=frame.image)
                roi_rect = self._roi_rect_for_frame(cam_id, frame_w, frame_h)
                visible_tracks = []
                cam_active = self.active_tracks[cam_id]
                current_active = set()
                frame_counters = {} if self.counters_enabled else None

                for track in tracks:
                    if not track.is_confirmed():
                        continue

                    if not self._is_allowed_class(track.det_class):
                        continue

                    if not self._track_inside_roi(track, roi_rect):
                        continue

                    visible_tracks.append(track)

                    if self.counters_enabled:
                        cls_name = track.det_class
                        frame_counters[cls_name] = frame_counters.get(cls_name, 0) + 1

                    track_id = track.track_id
                    current_active.add(track_id)

                    if track_id in cam_active:
                        continue

                    log_id = timestamp + str(track_id)
                    cam_active[track_id] = {
                        "log_id": log_id,
                        "start_time": timestamp,
                        "class_name": track.det_class,
                    }

                    self.log_task_queue.put_nowait(
                        {
                            "action": "start",
                            "id": log_id,
                            "datetimeStart": cam_active[track_id]["start_time"],
                            "cam_id": cam_id,
                            "event_type": track.det_class,
                            "src": "test",
                        }
                    )

                lost_ids = set(cam_active.keys()) - current_active
                for track_id in lost_ids:
                    log_info = cam_active[track_id]
                    self.log_task_queue.put_nowait(
                        {
                            "action": "end",
                            "log_id": log_info["log_id"],
                            "datetimeStop": timestamp,
                        }
                    )
                    del cam_active[track_id]

                self.draw_tracks(frame.image, visible_tracks, frame_counters)
                try:
                    self.out_queues[cam_id].put_nowait({"frame": frame})
                except queue.Full:
                    pass

    def _is_allowed_class(self, cls_name):
        if self.allowed_classes is None:
            return True
        return cls_name in self.allowed_classes

    def _roi_rect_for_frame(self, cam_id, frame_w, frame_h):
        if self.roi_state is None:
            return None

        roi = self.roi_state.get(cam_id)
        if roi is None:
            return None

        x1, y1, x2, y2 = roi
        left = max(0, min(frame_w - 1, int(round(x1 * frame_w))))
        top = max(0, min(frame_h - 1, int(round(y1 * frame_h))))
        right = max(0, min(frame_w - 1, int(round(x2 * frame_w))))
        bottom = max(0, min(frame_h - 1, int(round(y2 * frame_h))))

        if right <= left or bottom <= top:
            return None

        return left, top, right, bottom

    def _track_inside_roi(self, track, roi_rect):
        if roi_rect is None:
            return True

        x1, y1, x2, y2 = track.to_ltrb()
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        roi_x1, roi_y1, roi_x2, roi_y2 = roi_rect
        return roi_x1 <= center_x <= roi_x2 and roi_y1 <= center_y <= roi_y2

    def draw_tracks(self, frame, tracks, frame_counters):
        for track in tracks:
            x1, y1, x2, y2 = map(int, track.to_ltrb())
            track_id = track.track_id
            cls_name = track.det_class
            color = (0, 255, 0)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

            label = f"{cls_name} ID:{track_id}"
            cv2.putText(
                frame,
                label,
                (x1, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                1,
            )

        h, _ = frame.shape[:2]
        if self.counters_enabled and frame_counters:
            y_offset = h - 10

            for cls_name, count in frame_counters.items():
                text = f"{cls_name}: {count}"
                (_, text_h), _ = cv2.getTextSize(
                    text,
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    2,
                )

                cv2.putText(
                    frame,
                    text,
                    (10, y_offset),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 255),
                    2,
                )

                y_offset -= text_h + 10

    def stop(self):
        self.stop_evt.set()
