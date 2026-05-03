from datetime import datetime


SESSION_KEY = "session"
PREPROCESS_KEY = "preprocess"
INFERENCE_KEY = "inference"
POSTPROCESS_KEY = "postprocess"
DISPLAY_KEY = "display"


def capture_key(cam_id):
    return f"capture:{cam_id}"


def output_key(cam_id):
    return f"output:{cam_id}"


def display_key(cam_id):
    return f"display:{cam_id}"


def now_iso():
    return datetime.now().astimezone().isoformat(" ", "seconds")


def init_metrics_state(metrics_state, cameras, models, target_fps, configured_batch_size):
    metrics_state[SESSION_KEY] = {
        "status": "starting",
        "started_at": now_iso(),
        "camera_count": len(cameras),
        "model_count": len(models),
        "target_fps": target_fps,
        "configured_batch_size": configured_batch_size,
        "models": [model_path for _, model_path in models],
    }

    metrics_state[PREPROCESS_KEY] = {
        "batches_total": 0,
        "frames_total": 0,
        "last_batch_size": 0,
        "avg_batch_size": 0.0,
        "last_batch_ms": 0.0,
        "avg_batch_ms": 0.0,
        "fps": 0.0,
        "queue_overwrites": 0,
        "updated_at": now_iso(),
    }

    metrics_state[INFERENCE_KEY] = {
        "batches_total": 0,
        "frames_total": 0,
        "last_batch_size": 0,
        "last_inference_ms": 0.0,
        "avg_inference_ms": 0.0,
        "fps": 0.0,
        "queue_drops": 0,
        "gpu_allocated_mb": 0.0,
        "gpu_reserved_mb": 0.0,
        "gpu_peak_mb": 0.0,
        "updated_at": now_iso(),
    }

    metrics_state[POSTPROCESS_KEY] = {
        "frames_total": 0,
        "last_packet_ms": 0.0,
        "avg_packet_ms": 0.0,
        "visible_tracks": 0,
        "active_tracks": 0,
        "fps": 0.0,
        "updated_at": now_iso(),
    }

    metrics_state[DISPLAY_KEY] = {
        "frames_total": 0,
        "last_render_ms": 0.0,
        "avg_render_ms": 0.0,
        "last_latency_ms": 0.0,
        "avg_latency_ms": 0.0,
        "max_latency_ms": 0.0,
        "fps": 0.0,
        "updated_at": now_iso(),
    }

    for camera in cameras:
        cam_id = camera["id"]
        camera_name = camera.get("name") or f"Camera {cam_id}"
        metrics_state[capture_key(cam_id)] = {
            "camera_id": cam_id,
            "camera_name": camera_name,
            "fps": 0.0,
            "frames_total": 0,
            "queue_drops": 0,
            "read_errors": 0,
            "last_frame_at": "",
            "updated_at": now_iso(),
        }
        metrics_state[output_key(cam_id)] = {
            "camera_id": cam_id,
            "camera_name": camera_name,
            "fps": 0.0,
            "frames_total": 0,
            "queue_drops": 0,
            "visible_tracks": 0,
            "active_tracks": 0,
            "updated_at": now_iso(),
        }
        metrics_state[display_key(cam_id)] = {
            "camera_id": cam_id,
            "camera_name": camera_name,
            "fps": 0.0,
            "frames_total": 0,
            "last_render_ms": 0.0,
            "avg_render_ms": 0.0,
            "last_latency_ms": 0.0,
            "avg_latency_ms": 0.0,
            "max_latency_ms": 0.0,
            "updated_at": now_iso(),
        }


def mark_session_status(metrics_state, status):
    session = dict(metrics_state.get(SESSION_KEY, {}))
    session["status"] = status
    session["updated_at"] = now_iso()
    metrics_state[SESSION_KEY] = session
