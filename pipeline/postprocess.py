import os
import multiprocessing
import queue
import cv2
import time
from datetime import datetime

from deep_sort_realtime.deepsort_tracker import DeepSort
from gui.classDangerLevels import level_bgr
from pipeline.frameClass import Frame
from pipeline.runtime_metrics import POSTPROCESS_KEY, now_iso, output_key


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
        metrics_state=None,
        snapshot_dir=None,
        alert_queue=None,
        alert_decisions=None,
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
        self.metrics_state = metrics_state
        self.snapshot_dir = snapshot_dir
        self.alert_queue = alert_queue
        self.alert_decisions = alert_decisions

        self.active_tracks = {cam_id: {} for cam_id in cam_ids}
        self.pending_alerts = {}
        self.class_danger_levels = {}
        self.class_alert_settings = {}
        self.unknown_class_ids = set()
        if allowed_classes:
            self.allowed_classes = [cls[1] for cls in allowed_classes]
            self.class_danger_levels = {
                cls[1]: cls[3]
                for cls in allowed_classes
                if len(cls) > 3
            }
            self.class_alert_settings = {
                cls[1]: {
                    "alert_enabled": bool(cls[4]) if len(cls) > 4 else True,
                    "alert_delay_sec": float(cls[5]) if len(cls) > 5 else 0.0,
                }
                for cls in allowed_classes
            }
        else:
            self.allowed_classes = None

        self.counters_enabled = counters_enabled
        if self.snapshot_dir:
            os.makedirs(self.snapshot_dir, exist_ok=True)
        print("POSTPROCESS INIT")

    def run(self):
        packets_total = 0
        frames_total = 0
        frames_since_report = 0
        packet_ms_sum = 0.0
        last_report_at = time.monotonic()
        camera_stats = {
            cam_id: {
                "frames_total": 0,
                "frames_since_report": 0,
                "fps": 0.0,
                "queue_drops": 0,
                "visible_tracks": 0,
                "active_tracks": 0,
                "last_report_at": time.monotonic(),
            }
            for cam_id in self.cam_ids
        }

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

        while True:
            try:
                packet = self.to_process_queue.get(timeout=0.1)
            except queue.Empty:
                self._process_alert_decisions()
                if self.stop_evt.is_set():
                    break
                continue

            if packet is None:
                break

            packet_started_at = time.perf_counter()

            results = packet["results"]
            frames: list[Frame] = packet["FCs"]
            names = packet["names"]
            packet_visible_tracks = 0
            packet_active_tracks = 0

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
                        cls_id = int(cls)
                        cls_name = self._resolve_class_name(resnames, cls_id)
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
                    cls_name = track.det_class
                    current_active.add(track_id)

                    track_state = cam_active.get(track_id)
                    if track_state is not None and track_state["class_name"] != cls_name:
                        self._finalize_track_state(track_state, timestamp)
                        del cam_active[track_id]
                        track_state = None

                    if track_state is None:
                        log_id = f"{cam_id}:{track_id}:{timestamp}"
                        track_state = {
                            "cam_id": cam_id,
                            "track_id": track_id,
                            "class_name": cls_name,
                            "start_timestamp": timestamp,
                            "first_seen_monotonic": time.monotonic(),
                            "alert_pending": False,
                            "alert_rejected": False,
                            "db_started": False,
                            "log_id": log_id,
                            "snapshot_path": None,
                            "ended_timestamp": None,
                        }
                        cam_active[track_id] = track_state

                    if not self._alert_enabled(cls_name):
                        if not track_state["db_started"]:
                            self._start_event(
                                track_state["log_id"],
                                track_state["start_timestamp"],
                                cam_id,
                                cls_name,
                                src="event",
                            )
                            track_state["db_started"] = True
                        continue

                    if track_state["db_started"] or track_state["alert_pending"] or track_state["alert_rejected"]:
                        continue

                    if (time.monotonic() - track_state["first_seen_monotonic"]) < self._alert_delay_sec(cls_name):
                        continue

                    snapshot_path = self._save_alert_snapshot(frame.image, track, cam_id, cls_name, timestamp)
                    track_state["alert_pending"] = True
                    track_state["snapshot_path"] = snapshot_path
                    self.pending_alerts[track_state["log_id"]] = track_state
                    self._emit_pending_alert(track_state)

                lost_ids = set(cam_active.keys()) - current_active
                for track_id in lost_ids:
                    self._finalize_track_state(cam_active[track_id], timestamp)
                    del cam_active[track_id]

                packet_visible_tracks += len(visible_tracks)
                packet_active_tracks += len(cam_active)
                self._update_camera_stats(
                    cam_id,
                    camera_stats,
                    len(visible_tracks),
                    len(cam_active),
                )
                self.draw_tracks(frame.image, visible_tracks)
                try:
                    self.out_queues[cam_id].put_nowait(
                        {
                            "frame": frame,
                            "counters": dict(frame_counters or {}),
                        }
                    )
                except queue.Full:
                    camera_stats[cam_id]["queue_drops"] += 1

                self._maybe_publish_camera_metrics(cam_id, camera_stats)

            packet_ms = (time.perf_counter() - packet_started_at) * 1000.0
            packets_total += 1
            frames_total += len(frames)
            frames_since_report += len(frames)
            packet_ms_sum += packet_ms

            if time.monotonic() - last_report_at >= 1.0:
                report_interval = max(time.monotonic() - last_report_at, 1e-6)
                self._publish_global_metrics(
                    frames_total,
                    packet_ms,
                    packet_ms_sum / max(packets_total, 1),
                    packet_visible_tracks,
                    packet_active_tracks,
                    frames_since_report / report_interval,
                )
                frames_since_report = 0
                last_report_at = time.monotonic()

            self._process_alert_decisions()

        self._close_all_active_tracks(self._shutdown_timestamp())

    def _is_allowed_class(self, cls_name):
        if self.allowed_classes is None:
            return True
        return cls_name in self.allowed_classes

    def _alert_enabled(self, cls_name):
        settings = self.class_alert_settings.get(cls_name)
        if settings is None:
            return self.allowed_classes is None
        return bool(settings.get("alert_enabled"))

    def _alert_delay_sec(self, cls_name):
        settings = self.class_alert_settings.get(cls_name)
        if settings is None:
            return 0.0
        return max(0.0, float(settings.get("alert_delay_sec", 0.0)))

    def _start_event(self, log_id, timestamp, cam_id, cls_name, src="event", snapshot_path=None):
        self.log_task_queue.put_nowait(
            {
                "action": "start",
                "id": log_id,
                "datetimeStart": timestamp,
                "cam_id": cam_id,
                "event_type": cls_name,
                "src": src,
                "snapshot_path": snapshot_path,
            }
        )

    def _finish_event(self, track_state, timestamp):
        log_id = track_state.get("log_id")
        if not log_id:
            return

        self.log_task_queue.put_nowait(
            {
                "action": "end",
                "log_id": log_id,
                "datetimeStop": timestamp,
            }
        )

    def _emit_pending_alert(self, track_state):
        if self.alert_queue is None:
            return

        try:
            self.alert_queue.put_nowait(
                {
                    "id": track_state["log_id"],
                    "cam_id": track_state["cam_id"],
                    "track_id": track_state["track_id"],
                    "event_type": track_state["class_name"],
                    "datetimeStart": track_state["start_timestamp"],
                    "snapshot_path": track_state.get("snapshot_path"),
                    "danger_level": self.class_danger_levels.get(track_state["class_name"], "safe"),
                }
            )
        except queue.Full:
            print("[POSTPROCESS] Pending alert queue is full")

    def _process_alert_decisions(self):
        if self.alert_decisions is None:
            return

        for alert_id in list(self.alert_decisions.keys()):
            decision = self.alert_decisions.get(alert_id)
            try:
                del self.alert_decisions[alert_id]
            except KeyError:
                pass

            track_state = self.pending_alerts.get(alert_id)
            if track_state is None:
                continue

            if decision == "confirm":
                self._confirm_pending_alert(track_state)
            else:
                self._reject_pending_alert(track_state)

    def _confirm_pending_alert(self, track_state):
        if not track_state["db_started"]:
            self._start_event(
                track_state["log_id"],
                track_state["start_timestamp"],
                track_state["cam_id"],
                track_state["class_name"],
                src="alert",
                snapshot_path=track_state.get("snapshot_path"),
            )
            track_state["db_started"] = True

        track_state["alert_pending"] = False
        self.pending_alerts.pop(track_state["log_id"], None)

        if track_state.get("ended_timestamp"):
            self._finish_event(track_state, track_state["ended_timestamp"])

    def _reject_pending_alert(self, track_state):
        track_state["alert_pending"] = False
        track_state["alert_rejected"] = True
        self.pending_alerts.pop(track_state["log_id"], None)
        self._delete_snapshot(track_state)

    def _finalize_track_state(self, track_state, timestamp):
        if track_state.get("db_started"):
            self._finish_event(track_state, timestamp)
            self.pending_alerts.pop(track_state["log_id"], None)
            return

        if track_state.get("alert_pending"):
            track_state["ended_timestamp"] = timestamp
            return

        self._delete_snapshot(track_state)

    def _delete_snapshot(self, track_state):
        snapshot_path = track_state.get("snapshot_path")
        if not snapshot_path:
            return

        try:
            if os.path.exists(snapshot_path):
                os.remove(snapshot_path)
        except OSError as exc:
            print(f"[POSTPROCESS] Failed to delete snapshot: {exc}")

        track_state["snapshot_path"] = None

    def _close_all_active_tracks(self, timestamp):
        self._process_alert_decisions()

        for cam_tracks in self.active_tracks.values():
            for track_state in list(cam_tracks.values()):
                self._finalize_track_state(track_state, timestamp)
            cam_tracks.clear()

        for track_state in list(self.pending_alerts.values()):
            if track_state.get("db_started") and track_state.get("ended_timestamp"):
                self._finish_event(track_state, track_state["ended_timestamp"])
            elif not track_state.get("db_started"):
                self._delete_snapshot(track_state)

        self.pending_alerts.clear()

    @staticmethod
    def _shutdown_timestamp():
        return datetime.now().astimezone().isoformat(" ", "seconds")

    def _resolve_class_name(self, resnames, cls_id):
        if isinstance(resnames, dict):
            if cls_id in resnames:
                return str(resnames[cls_id])

            string_key = str(cls_id)
            if string_key in resnames:
                return str(resnames[string_key])
        elif isinstance(resnames, (list, tuple)):
            if 0 <= cls_id < len(resnames):
                return str(resnames[cls_id])

        if cls_id not in self.unknown_class_ids:
            print(f"[POSTPROCESS] Unknown class id {cls_id} in model names mapping")
            self.unknown_class_ids.add(cls_id)
        return f"class_{cls_id}"

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

    def draw_tracks(self, frame, tracks):
        for track in tracks:
            x1, y1, x2, y2 = map(int, track.to_ltrb())
            track_id = track.track_id
            cls_name = track.det_class
            color = self._track_color(cls_name)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

            label = f"{cls_name}"
            cv2.putText(
                frame,
                label,
                (x1, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                1,
            )

    def _track_color(self, cls_name):
        danger_level = self.class_danger_levels.get(cls_name, "safe")
        return level_bgr(danger_level)

    def _save_alert_snapshot(self, frame, track, cam_id, cls_name, timestamp):
        if not self.snapshot_dir:
            return None

        try:
            image = frame.copy()
            x1, y1, x2, y2 = map(int, track.to_ltrb())
            color = self._track_color(cls_name)
            cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
            cv2.putText(
                image,
                f"{cls_name} ID:{track.track_id}",
                (x1, max(20, y1 - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                color,
                2,
            )

            safe_timestamp = timestamp.replace(":", "-").replace(" ", "_")
            safe_class_name = "".join(
                char if char.isalnum() or char in ("-", "_") else "_"
                for char in str(cls_name)
            )
            filename = f"cam_{cam_id}_{safe_class_name}_{safe_timestamp}_{track.track_id}.jpg"
            snapshot_path = os.path.abspath(os.path.join(self.snapshot_dir, filename))

            if cv2.imwrite(snapshot_path, image):
                return snapshot_path
        except Exception as exc:
            print(f"[POSTPROCESS] Failed to save snapshot: {exc}")

        return None

    def _update_camera_stats(self, cam_id, camera_stats, visible_tracks, active_tracks):
        stats = camera_stats[cam_id]
        stats["frames_total"] += 1
        stats["frames_since_report"] += 1
        stats["visible_tracks"] = visible_tracks
        stats["active_tracks"] = active_tracks

    def _maybe_publish_camera_metrics(self, cam_id, camera_stats):
        if self.metrics_state is None:
            return

        stats = camera_stats[cam_id]
        now_monotonic = time.monotonic()
        report_interval = now_monotonic - stats["last_report_at"]
        if report_interval < 1.0:
            return

        fps = stats["frames_since_report"] / max(report_interval, 1e-6)
        previous = self.metrics_state.get(output_key(cam_id), {})
        self.metrics_state[output_key(cam_id)] = {
            "camera_id": cam_id,
            "camera_name": previous.get("camera_name", f"Camera {cam_id}"),
            "fps": round(fps, 2),
            "frames_total": stats["frames_total"],
            "queue_drops": stats["queue_drops"],
            "visible_tracks": stats["visible_tracks"],
            "active_tracks": stats["active_tracks"],
            "updated_at": now_iso(),
        }
        stats["frames_since_report"] = 0
        stats["last_report_at"] = now_monotonic

    def _publish_global_metrics(
        self,
        frames_total,
        last_packet_ms,
        avg_packet_ms,
        visible_tracks,
        active_tracks,
        fps,
    ):
        if self.metrics_state is None:
            return

        self.metrics_state[POSTPROCESS_KEY] = {
            "frames_total": frames_total,
            "last_packet_ms": round(last_packet_ms, 2),
            "avg_packet_ms": round(avg_packet_ms, 2),
            "visible_tracks": visible_tracks,
            "active_tracks": active_tracks,
            "fps": round(fps, 2),
            "updated_at": now_iso(),
        }

    def stop(self):
        self.stop_evt.set()
        try:
            self.to_process_queue.put_nowait(None)
        except queue.Full:
            pass
