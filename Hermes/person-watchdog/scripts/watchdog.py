#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PersonWatchdog v2 - 检测摄像头前经过的人，并通过 Hermes 发送飞书通知。

v2 改进：
- 发送无 cmd 弹窗（CREATE_NO_WINDOW）+ 后台队列异步发送
- 稳定检测（连续 3 帧确认）+ 采集窗口（默认 6 秒）+ 最佳帧评分（清晰人脸优先）
- 停留时长：出现 / 离开两条低频通知
- 省电：空闲时仅运动门控（160 宽灰度帧差），不跑 YOLO
- 自动学习：误报区域记忆 + 自适应置信度阈值，持久化 learning_data.json
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import logging
import queue
import shutil
import subprocess
import sys
import threading
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path

import numpy as np

APP_NAME = "PersonWatchdog"
APP_VERSION = "2.2.1"
BASE_DIR = Path(__file__).resolve().parent

# Windows 下隐藏子进程控制台窗口；非 Windows 平台为 0
CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)

DEFAULT_CONFIG = {
    # 摄像头
    "camera_index": 0,
    "auto_select_camera": True,
    "camera_name_include": [],
    "camera_name_exclude": ["OBS", "Virtual", "OMEN"],
    "allow_virtual_fallback": False,
    "min_frame_brightness": 8.0,
    "warmup_frames": 10,
    # 人体检测（YOLO11m ONNX）
    "model": "yolo11m.onnx",
    "models_dir": "models",
    "conf_threshold": 0.35,
    "nms_threshold": 0.45,
    "input_size": 640,
    "onnx_threads": 4,
    # 人脸检测（YuNet ONNX，采集窗口内懒加载）
    "face_model": "face_detection_yunet_2023mar.onnx",
    "min_face_conf": 0.6,
    "min_face_ratio": 0.06,
    # 时序
    "active_interval_ms": 200,
    "capture_interval_ms": 250,
    "present_interval_ms": 1000,
    "idle_interval_ms": 500,
    "idle_detect_secs": 5.0,
    "idle_empty_backoff_secs": 2.0,
    "human_confirm_frames": 3,
    "capture_window_secs": 6,
    "exit_confirm_secs": 5,
    "grace_secs": 15,
    # 运动门控（省电）
    "motion_gate_width": 160,
    "motion_threshold": 18.0,
    "motion_learn_rate": 0.05,
    # 最佳帧评分
    "clarity_norm_k": 1000.0,
    # 自动学习
    "learning_data": "learning_data.json",
    "learning_grid": 6,
    "false_region_repeat": 3,
    "false_region_suppress_factor": 0.4,
    "false_alarm_max_secs": 5.0,
    "adaptive_threshold_min": 0.25,
    "adaptive_threshold_max": 0.55,
    "adaptive_threshold_step": 0.02,
    # 通知
    "hermes_send": r"T:\programming\project\Hermes\hermes-agent\venv\Scripts\hermes.exe",
    "target": "feishu:oc_4cc326a0f558eb53676559ab60201a9c",
    "appear_template": "⚠️ 有人出现在电脑前（{time}）",
    "leave_template": "👋 人已离开，停留 {duration}",
    "message_template": "⚠️ 有人经过你的电脑前（{time}）",
    "notify_on_leave": True,
    "send_snapshot": True,
    "snapshot_dir": "snapshots",
    "keep_snapshots": False,
}


_SINGLE_INSTANCE_MUTEX = None


def acquire_single_instance() -> bool:
    """Windows 命名互斥量 + 非 Windows 锁文件：防止多个 watchdog 同时占用摄像头。"""
    global _SINGLE_INSTANCE_MUTEX
    if sys.platform == "win32":
        try:
            import ctypes

            _SINGLE_INSTANCE_MUTEX = ctypes.windll.kernel32.CreateMutexW(None, False, "PersonWatchdogMutex")
            return ctypes.windll.kernel32.GetLastError() != 183  # ERROR_ALREADY_EXISTS
        except Exception:
            return True
    try:
        lock = BASE_DIR / "watchdog.lock"
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode("ascii"))
        os.close(fd)
        return True
    except FileExistsError:
        return False
    except Exception:
        return True


def setup_logging():
    log_dir = BASE_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(
        log_dir / "watchdog.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    handlers = [handler]
    if sys.stderr is not None:
        handlers.append(logging.StreamHandler())
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=handlers,
    )


log = logging.getLogger("person-watchdog")


def load_config(path: Path) -> dict:
    cfg = dict(DEFAULT_CONFIG)
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            cfg.update(data)
        except Exception as exc:
            log.warning("配置文件解析失败，使用默认配置: %s", exc)
    return cfg


def resolve_hermes(cfg: dict) -> str:
    exe = cfg.get("hermes_send") or ""
    if exe and Path(exe).exists():
        return exe
    found = shutil.which("hermes")
    if found:
        return found
    return exe or "hermes"


def open_camera(index: int):
    import cv2

    cap = cv2.VideoCapture(int(index), cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap.release()
        cap = cv2.VideoCapture(int(index))
    if not cap.isOpened():
        raise RuntimeError(f"无法打开摄像头 index={index}")
    return cap


def frame_brightness(frame: np.ndarray) -> float:
    """返回整帧平均亮度（0-255）。"""
    return float(frame.mean())


def probe_cameras() -> list:
    """枚举摄像头，返回 (index, 亮度, 宽, 高)；打不开或读不到帧时亮度为 None。"""
    found = []
    for i in range(8):
        cap = None
        try:
            cap = open_camera(i)
            brightness = None
            w = h = 0
            for _ in range(3):
                ok, frame = cap.read()
                if ok and frame is not None:
                    brightness = frame_brightness(frame)
                    w, h = frame.shape[1], frame.shape[0]
                    break
            found.append((i, brightness, w, h))
        except Exception:
            found.append((i, None, 0, 0))
        finally:
            if cap is not None:
                cap.release()
    return found


def list_device_names():
    """返回按 DirectShow 顺序排列的摄像头设备名；枚举失败返回 None。"""
    try:
        logging.getLogger("comtypes").setLevel(logging.WARNING)
        from pygrabber.dshow_graph import FilterGraph

        return list(FilterGraph().get_input_devices())
    except Exception:
        return None


def _select_by_brightness(cfg: dict, pref: int) -> int:
    """亮度法兜底：在可用摄像头里挑最亮的。"""
    probes = probe_cameras()
    min_b = float(cfg.get("min_frame_brightness", 8.0))
    good = [x for x in probes if x[1] is not None and x[1] >= min_b]
    if not good:
        log.warning("所有摄像头画面均过暗/黑屏（可能被占用、遮挡或隐私关闭），继续使用配置的 index=%d", pref)
        return pref
    best = max(good, key=lambda x: x[1])
    if pref not in [x[0] for x in good]:
        log.warning("配置的摄像头 index=%d 画面过黑，自动切换到 index=%d（亮度 %.1f）", pref, best[0], best[1])
        return best[0]
    return pref


def select_camera(cfg: dict) -> int:
    """选择摄像头：优先按设备名挑物理摄像头（排除 OBS/OMEN 等虚拟设备），拿不到设备名时退回亮度法。"""
    pref = int(cfg.get("camera_index", 0))
    names = list_device_names()
    if names is None:
        if not cfg.get("auto_select_camera", True):
            return pref
        return _select_by_brightness(cfg, pref)

    include = [s.lower() for s in cfg.get("camera_name_include", [])]
    exclude = [s.lower() for s in cfg.get("camera_name_exclude", ["OBS", "Virtual", "OMEN"])]
    candidates = []
    for i, name in enumerate(names):
        low = name.lower()
        if any(s in low for s in exclude):
            continue
        if include and not any(s in low for s in include):
            continue
        candidates.append((i, name))
    if candidates:
        idx, name = candidates[0]
        if idx != pref:
            log.info("按设备名选择摄像头: index=%d (%s)", idx, name)
        return idx
    if not cfg.get("allow_virtual_fallback", False):
        log.warning("未找到非虚拟摄像头（排除词 %s），可用设备: %s；若摄像头被占用请关闭占用程序后重试", exclude, names)
        return pref
    if cfg.get("auto_select_camera", True):
        return _select_by_brightness(cfg, pref)
    return pref


def list_cameras() -> list:
    return probe_cameras()


def grab_warmed_frame(cap, cfg: dict):
    """连续读取若干帧直到画面亮度达标（避免首帧黑屏/曝光未就绪）。返回 (frame, brightness)。"""
    min_b = float(cfg.get("min_frame_brightness", 8.0))
    max_tries = max(1, int(cfg.get("warmup_frames", 10)))
    last = None
    last_b = None
    for _ in range(max_tries):
        ok, frame = cap.read()
        if ok and frame is not None:
            last = frame
            last_b = frame_brightness(frame)
            if last_b >= min_b:
                return last, last_b
    return last, last_b


# ---------------------------------------------------------------------------
# 通用小工具
# ---------------------------------------------------------------------------

def format_duration(seconds) -> str:
    """把秒数格式化为 'X 分 Y 秒' / 'X 小时 Y 分 Z 秒'。"""
    seconds = max(0, int(round(float(seconds))))
    hours, rem = divmod(seconds, 3600)
    mins, secs = divmod(rem, 60)
    if hours:
        return f"{hours} 小时 {mins} 分 {secs} 秒"
    if mins:
        return f"{mins} 分 {secs} 秒"
    return f"{secs} 秒"


def clarity_of(frame: np.ndarray) -> float:
    """Laplacian 方差：越大表示画面越清晰/边缘越锐利。"""
    import cv2

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if frame.ndim == 3 else frame
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def letterbox(img: np.ndarray, size: int, color=(114, 114, 114)):
    import cv2

    h, w = img.shape[:2]
    r = min(size / w, size / h)
    new_w, new_h = round(w * r), round(h * r)
    resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
    canvas = np.full((size, size, 3), color, dtype=np.uint8)
    pad_x = (size - new_w) // 2
    pad_y = (size - new_h) // 2
    canvas[pad_y : pad_y + new_h, pad_x : pad_x + new_w] = resized
    return canvas, r, pad_x, pad_y


def nms(boxes: np.ndarray, scores: np.ndarray, iou_thr: float) -> list:
    boxes = np.asarray(boxes, dtype=np.float64)
    scores = np.asarray(scores, dtype=np.float64)
    if len(boxes) == 0:
        return []
    x1, y1, x2, y2 = boxes[:, 0], boxes[:, 1], boxes[:, 2], boxes[:, 3]
    areas = (x2 - x1) * (y2 - y1)
    order = scores.argsort()[::-1]
    keep = []
    while order.size:
        i = order[0]
        keep.append(int(i))
        rest = order[1:]
        if rest.size == 0:
            break
        xx1 = np.maximum(x1[i], x1[rest])
        yy1 = np.maximum(y1[i], y1[rest])
        xx2 = np.minimum(x2[i], x2[rest])
        yy2 = np.minimum(y2[i], y2[rest])
        inter = np.maximum(0.0, xx2 - xx1) * np.maximum(0.0, yy2 - yy1)
        iou = inter / (areas[i] + areas[rest] - inter)
        order = rest[iou <= iou_thr]
    return keep


def suppress_detections(detections, regions, factor: float) -> list:
    """把中心点落在抑制区域内的检测框置信度乘以 factor（用于误报区域记忆）。"""
    if not regions:
        return detections
    out = []
    for x1, y1, x2, y2, score in detections:
        cx = (x1 + x2) / 2.0
        cy = (y1 + y2) / 2.0
        hit = False
        for rx1, ry1, rx2, ry2 in regions:
            if rx1 <= cx <= rx2 and ry1 <= cy <= ry2:
                hit = True
                break
        out.append((x1, y1, x2, y2, score * float(factor) if hit else score))
    return out


def detect_people(session, frame: np.ndarray, cfg: dict, conf=None, suppress_regions=None) -> list:
    """YOLO 人体检测，返回 [(x1,y1,x2,y2,score), ...]（原始帧坐标）。"""
    size = int(cfg["input_size"])
    canvas, ratio, pad_x, pad_y = letterbox(frame, size)
    blob = canvas[:, :, ::-1].transpose(2, 0, 1)[None].astype(np.float32) / 255.0
    input_name = session.get_inputs()[0].name
    out = session.run(None, {input_name: blob})[0]
    if out.ndim == 3:
        out = out[0]
    if out.shape[0] == 84:
        out = out.T  # (N, 84): cx, cy, w, h + 80 class scores
    cx, cy, w, h = out[:, 0], out[:, 1], out[:, 2], out[:, 3]
    person_scores = out[:, 4].astype(np.float64).copy()
    xs = (cx - w / 2.0 - pad_x) / ratio
    ys = (cy - h / 2.0 - pad_y) / ratio
    xe = (cx + w / 2.0 - pad_x) / ratio
    ye = (cy + h / 2.0 - pad_y) / ratio
    boxes = np.stack([xs, ys, xe, ye], axis=1)
    boxes[:, 0] = np.clip(boxes[:, 0], 0, frame.shape[1])
    boxes[:, 1] = np.clip(boxes[:, 1], 0, frame.shape[0])
    boxes[:, 2] = np.clip(boxes[:, 2], 0, frame.shape[1])
    boxes[:, 3] = np.clip(boxes[:, 3], 0, frame.shape[0])

    if suppress_regions:
        factor = float(cfg.get("false_region_suppress_factor", 0.4))
        for i in range(len(person_scores)):
            bcx = (boxes[i, 0] + boxes[i, 2]) / 2.0
            bcy = (boxes[i, 1] + boxes[i, 3]) / 2.0
            for rx1, ry1, rx2, ry2 in suppress_regions:
                if rx1 <= bcx <= rx2 and ry1 <= bcy <= ry2:
                    person_scores[i] *= factor
                    break

    conf_thr = float(cfg["conf_threshold"]) if conf is None else float(conf)
    idx = np.arange(len(person_scores))
    mask = person_scores >= conf_thr
    if not mask.any():
        return []
    sel = idx[mask]
    keep = nms(boxes[sel], person_scores[sel], float(cfg["nms_threshold"]))
    return [
        (
            float(boxes[sel[i], 0]),
            float(boxes[sel[i], 1]),
            float(boxes[sel[i], 2]),
            float(boxes[sel[i], 3]),
            float(person_scores[sel[i]]),
        )
        for i in keep
    ]


# ---------------------------------------------------------------------------
# 省电运动门控
# ---------------------------------------------------------------------------

class MotionGate:
    """空闲时只做 160 宽灰度帧差，学习光照变化，不跑 YOLO。"""

    def __init__(self, width=160, threshold=18.0, learn_rate=0.05):
        self.width = int(width)
        self.threshold = float(threshold)
        self.learn_rate = float(learn_rate)
        self._bg = None
        self.last_motion = False

    def reset(self):
        self._bg = None
        self.last_motion = False

    def downscale(self, frame: np.ndarray) -> np.ndarray:
        import cv2

        h, w = frame.shape[:2]
        scale = self.width / max(1, w)
        nh = max(2, int(round(h * scale)))
        small = cv2.resize(frame, (self.width, nh), interpolation=cv2.INTER_AREA)
        return cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)

    def update(self, gray_small: np.ndarray) -> bool:
        g = np.asarray(gray_small, dtype=np.float32)
        if self._bg is None:
            self._bg = g.copy()
            self.last_motion = False
            return False
        diff = float(np.abs(g - self._bg).mean())
        motion = diff > self.threshold
        lr = self.learn_rate * (0.25 if motion else 1.0)  # 有运动时背景更新更慢
        self._bg = self._bg * (1.0 - lr) + g * lr
        self.last_motion = motion
        return motion

# ---------------------------------------------------------------------------
# 人脸检测（YuNet，懒加载）
# ---------------------------------------------------------------------------

class FaceDetector:
    """基于 OpenCV FaceDetectorYN（YuNet ONNX）的人脸检测，首次使用时才加载模型。"""

    def __init__(self, model_path, cfg: dict):
        self.model_path = str(model_path)
        self.min_conf = float(cfg.get("min_face_conf", 0.6))
        self.nms_threshold = 0.3
        self._detector = None

    def _ensure(self):
        if self._detector is None:
            import cv2

            try:
                cv2.utils.logging.setLogLevel(cv2.utils.logging.LOG_LEVEL_ERROR)
            except Exception:
                pass
            self._detector = cv2.FaceDetectorYN.create(
                self.model_path, "", (320, 320), self.min_conf, self.nms_threshold, 5000
            )
        return self._detector

    def is_loaded(self) -> bool:
        return self._detector is not None

    def detect(self, frame: np.ndarray) -> list:
        det = self._ensure()
        h, w = frame.shape[:2]
        det.setInputSize((w, h))
        ok, faces = det.detect(frame)
        out = []
        if ok and faces is not None:
            for f in faces:
                x, y, fw, fh = float(f[0]), float(f[1]), float(f[2]), float(f[3])
                conf = float(f[14])
                if conf >= self.min_conf and fw > 0 and fh > 0:
                    out.append((x, y, x + fw, y + fh, conf))
        return out


# ---------------------------------------------------------------------------
# 最佳帧评分
# ---------------------------------------------------------------------------

def _norm_clarity(clarity: float, k: float) -> float:
    return clarity / (clarity + max(float(k), 1e-6))


def best_shot_score(frame: np.ndarray, detections, faces, cfg: dict):
    """综合评分：人脸占比 x 人脸置信度 x 清晰度；无人脸时退回最大人体框 x 清晰度。

    返回 (score, clarity)。
    """
    k = float(cfg.get("clarity_norm_k", 1000.0))
    min_ratio = float(cfg.get("min_face_ratio", 0.06))
    h, w = frame.shape[:2]
    area = max(1.0, float(w * h))
    clarity = clarity_of(frame)
    cnorm = _norm_clarity(clarity, k)

    if faces:
        best_face = 0.0
        for x1, y1, x2, y2, conf in faces:
            ratio = max(0.0, (x2 - x1) * (y2 - y1)) / area
            if ratio < min_ratio:
                continue
            best_face = max(best_face, ratio * float(conf))
        if best_face > 0.0:
            return best_face * cnorm, clarity

    body = 0.0
    for x1, y1, x2, y2, _score in detections or []:
        ratio = max(0.0, (x2 - x1) * (y2 - y1)) / area
        body = max(body, ratio)
    return body * cnorm, clarity


class BestShot:
    """采集窗口内累计最高分帧。"""

    def __init__(self, cfg: dict):
        self.cfg = cfg
        self._best_frame = None
        self._best_dets = []
        self._best_faces = []
        self._best_score = -1.0

    def push(self, frame: np.ndarray, detections, faces):
        score, _clarity = best_shot_score(frame, detections, faces, self.cfg)
        if score > self._best_score:
            self._best_score = score
            self._best_frame = frame.copy()
            self._best_dets = list(detections or [])
            self._best_faces = list(faces or [])

    @property
    def has_face(self) -> bool:
        return bool(self._best_faces)

    def best(self):
        if self._best_frame is None:
            return None
        return self._best_frame, self._best_dets, self._best_faces


# ---------------------------------------------------------------------------
# 自动学习（误报区域记忆 + 自适应阈值）
# ---------------------------------------------------------------------------

class LearningMemory:
    """纯自动本地学习：同一区域重复误报则抑制该区域；按事件质量自适应阈值。"""

    def __init__(self, path, cfg: dict):
        self.path = Path(path)
        self.cfg = cfg
        self._min = float(cfg.get("adaptive_threshold_min", 0.25))
        self._max = float(cfg.get("adaptive_threshold_max", 0.55))
        self._step = float(cfg.get("adaptive_threshold_step", 0.02))
        self._repeat = max(1, int(cfg.get("false_region_repeat", 3)))
        self._factor = float(cfg.get("false_region_suppress_factor", 0.4))
        self._max_false_secs = float(cfg.get("false_alarm_max_secs", 5.0))
        self._grid = max(2, int(cfg.get("learning_grid", 6)))
        self._data = {"threshold": float(cfg.get("conf_threshold", 0.35)), "regions": {}}
        self._suppressed = set()
        self.load()

    # ---- 持久化 ----
    def load(self):
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return
        if not isinstance(data, dict):
            return
        if isinstance(data.get("threshold"), (int, float)):
            self._data["threshold"] = float(data["threshold"])
        if isinstance(data.get("regions"), dict):
            self._data["regions"] = {str(k): int(v) for k, v in data["regions"].items()}
        self._clamp()
        self._rebuild_suppressed()

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_name(self.path.name + ".tmp")
        tmp.write_text(json.dumps(self._data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    def reset(self):
        self._data = {"threshold": float(self.cfg.get("conf_threshold", 0.35)), "regions": {}}
        self._suppressed = set()
        self.save()

    # ---- 阈值 ----
    def _clamp(self):
        self._data["threshold"] = min(max(self._data["threshold"], self._min), self._max)

    @property
    def threshold(self) -> float:
        return self._data["threshold"]

    # ---- 误报区域 ----
    def _rebuild_suppressed(self):
        self._suppressed = {k for k, v in self._data["regions"].items() if v >= self._repeat}

    def region_key(self, x1, y1, x2, y2, frame_w, frame_h) -> str:
        cx = (x1 + x2) / 2.0
        cy = (y1 + y2) / 2.0
        gx = min(self._grid - 1, max(0, int(cx / max(1.0, frame_w) * self._grid)))
        gy = min(self._grid - 1, max(0, int(cy / max(1.0, frame_h) * self._grid)))
        return f"{gx}_{gy}"

    def note_false_alarm(self, detections, frame_shape):
        h, w = frame_shape[0], frame_shape[1]
        for x1, y1, x2, y2, _s in detections or []:
            key = self.region_key(x1, y1, x2, y2, w, h)
            self._data["regions"][key] = self._data["regions"].get(key, 0) + 1
        self._rebuild_suppressed()
        self.save()

    def is_suppressed(self, key: str) -> bool:
        return key in self._suppressed

    def suppression_factor(self, key: str) -> float:
        return self._factor if key in self._suppressed else 1.0

    def suppressed_regions(self, frame_shape) -> list:
        h, w = frame_shape[0], frame_shape[1]
        cw = max(1.0, w / self._grid)
        ch = max(1.0, h / self._grid)
        out = []
        for key in sorted(self._suppressed):
            gx, gy = key.split("_")
            out.append((int(gx) * cw, int(gy) * ch, (int(gx) + 1) * cw, (int(gy) + 1) * ch))
        return out

    # ---- 事件学习 ----
    def learn_from_event(self, event: dict, detections=None, frame_shape=None):
        had_face = bool(event.get("had_face"))
        duration = float(event.get("duration", 0.0))
        if not had_face and duration < self._max_false_secs:
            self._data["threshold"] = min(self._max, self._data["threshold"] + self._step)
            if detections and frame_shape is not None:
                self.note_false_alarm(detections, frame_shape)
        else:
            self._data["threshold"] = max(self._min, self._data["threshold"] - self._step)
        self.save()

# ---------------------------------------------------------------------------
# 状态机（定义“有人经过”）
# ---------------------------------------------------------------------------

class PresenceTracker:
    IDLE = "IDLE"
    CAPTURING = "CAPTURING"
    PRESENT = "PRESENT"

    def __init__(self, cfg: dict, clock=time.monotonic):
        self.cfg = cfg
        self.confirm_frames = max(1, int(cfg.get("human_confirm_frames", 3)))
        self.capture_window_secs = float(cfg.get("capture_window_secs", 6))
        self.exit_confirm_secs = float(cfg.get("exit_confirm_secs", 5))
        self.grace_secs = float(cfg.get("grace_secs", 15))
        self.clock = clock
        self.start_time = clock()
        self.state = self.IDLE
        self._confirm_count = 0
        self._absent_since = None
        self._appear_time = None
        self._capture_until = None
        self._best = None

    def armed(self) -> bool:
        return (self.clock() - self.start_time) >= self.grace_secs

    @property
    def in_confirm(self) -> bool:
        """IDLE 下已累计到部分确认帧（连续检测有人中），用于让检测循环保持活跃。"""
        return self._confirm_count > 0

    def _reset(self):
        self.state = self.IDLE
        self._confirm_count = 0
        self._absent_since = None
        self._appear_time = None
        self._capture_until = None
        self._best = None

    def tick(self, present: bool, frame=None, detections=None, faces=None) -> list:
        """每帧调用一次。返回事件列表：appear / leave。"""
        if not self.armed():
            self._reset()
            return []
        now = self.clock()
        events = []

        if self.state == self.IDLE:
            if present:
                self._confirm_count += 1
                if self._confirm_count >= self.confirm_frames:
                    self.state = self.CAPTURING
                    self._appear_time = now
                    self._capture_until = now + self.capture_window_secs
                    self._best = BestShot(self.cfg)
                    if frame is not None:
                        self._best.push(frame, detections, faces)
            else:
                self._confirm_count = 0
            return events

        if self.state == self.CAPTURING:
            if present:
                self._absent_since = None
                if frame is not None and self._best is not None:
                    self._best.push(frame, detections, faces)
            else:
                if self._absent_since is None:
                    self._absent_since = now
                elif now - self._absent_since >= self.exit_confirm_secs:
                    # 采集窗口内人已离开：先补发出现，再发离开
                    events.append(self._appear_event())
                    events.append(self._leave_event(now))
                    self._reset()
                    return events
            if now >= self._capture_until:
                events.append(self._appear_event())
                self.state = self.PRESENT
            return events

        # PRESENT
        if present:
            self._absent_since = None
        else:
            if self._absent_since is None:
                self._absent_since = now
            elif now - self._absent_since >= self.exit_confirm_secs:
                events.append(self._leave_event(now))
                self._reset()
        return events

    def _appear_event(self) -> dict:
        best = self._best.best() if self._best is not None else None
        return {
            "type": "appear",
            "time": self._appear_time,
            "frame": best[0] if best else None,
            "detections": best[1] if best else [],
            "faces": best[2] if best else [],
            "had_face": bool(best[2]) if best else False,
        }

    def _leave_event(self, now: float) -> dict:
        best = self._best.best() if self._best is not None else None
        return {
            "type": "leave",
            "duration": max(0.0, now - (self._appear_time or now)),
            "had_face": bool(self._best is not None and self._best.has_face),
            "detections": best[1] if best else [],
            "frame": best[0] if best else None,
        }


# ---------------------------------------------------------------------------
# 通知发送（无弹窗 + 后台队列）
# ---------------------------------------------------------------------------

def send_message(cfg: dict, text: str, media_path=None, timeout=90) -> bool:
    hermes = resolve_hermes(cfg)
    msg = text if media_path is None else f"{text}\nMEDIA:{media_path}"
    cmd = [hermes, "send", "--to", str(cfg["target"]), msg]
    log.info("发送通知 -> %s (hermes=%s)", cfg["target"], hermes)
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            creationflags=CREATE_NO_WINDOW,
        )
    except subprocess.TimeoutExpired:
        log.error("hermes send 超时")
        return False
    except FileNotFoundError:
        log.error("找不到 hermes 命令: %s（请检查 config.json 的 hermes_send）", hermes)
        return False
    if proc.returncode == 0:
        log.info("通知发送成功: %s", (proc.stdout or "").strip())
        return True
    log.error(
        "hermes send 失败 rc=%s stdout=%s stderr=%s",
        proc.returncode,
        (proc.stdout or "").strip(),
        (proc.stderr or "").strip(),
    )
    return False


class Sender:
    """后台线程发送，不阻塞检测循环；发送成功且不保留时删除本地抓拍。"""

    def __init__(self, cfg: dict):
        self.cfg = cfg
        self._queue = queue.Queue()
        self._lock = threading.Lock()
        self._pending = 0
        self._idle = threading.Event()
        self._idle.set()
        self._thread = threading.Thread(target=self._worker, name="watchdog-sender", daemon=True)
        self._thread.start()

    def _worker(self):
        while True:
            item = self._queue.get()
            if item is None:
                return
            text, media = item
            try:
                sent = send_message(self.cfg, text, media)
                if media is not None and Path(media).exists():
                    if sent and not self.cfg.get("keep_snapshots", False):
                        Path(media).unlink(missing_ok=True)
                        log.info("抓拍已发送并删除: %s", media)
                    elif not sent:
                        log.info("通知失败，保留抓拍以便补发: %s", media)
            except Exception as exc:
                log.error("后台发送异常: %s", exc)
            finally:
                with self._lock:
                    self._pending -= 1
                    if self._pending <= 0:
                        self._idle.set()

    def send(self, text: str, media_path=None):
        with self._lock:
            self._pending += 1
            self._idle.clear()
        self._queue.put((text, media_path))

    def flush(self, timeout=120) -> bool:
        return self._idle.wait(timeout)

    def close(self, timeout=120) -> bool:
        """停止 worker：先排空队列中已入队的消息，再等待线程退出。返回是否干净退出。"""
        self._queue.put(None)
        self._thread.join(timeout)
        if self._thread.is_alive():
            log.warning("发送线程在 %.0f 秒内未退出，仍有消息未发送", timeout)
            return False
        return True


# ---------------------------------------------------------------------------
# 抓拍
# ---------------------------------------------------------------------------

def save_snapshot(cfg: dict, frame: np.ndarray, detections=None, faces=None):
    import cv2

    img = frame.copy()
    for x1, y1, x2, y2, score in detections or []:
        cv2.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), (0, 0, 255), 2)
        cv2.putText(
            img, f"person {score:.2f}", (int(x1), max(0, int(y1) - 6)),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1,
        )
    for x1, y1, x2, y2, conf in faces or []:
        cv2.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
        cv2.putText(
            img, f"face {conf:.2f}", (int(x1), max(0, int(y1) - 6)),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1,
        )
    ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    snap_dir = Path(cfg["snapshot_dir"])
    if not snap_dir.is_absolute():
        snap_dir = BASE_DIR / snap_dir
    snap_dir.mkdir(parents=True, exist_ok=True)
    path = snap_dir / f"person_{ts}.jpg"
    if not cv2.imwrite(str(path), img):
        log.error("抓拍图保存失败: %s", path)
        return None
    log.info("抓拍已保存: %s", path)
    return path


# ---------------------------------------------------------------------------
# CLI 子命令
# ---------------------------------------------------------------------------

def cmd_test_send(cfg: dict, text: str) -> int:
    if not acquire_single_instance():
        log.error("已有 PersonWatchdog 实例在运行，请先停止它再执行 --test-send（否则摄像头被占用会拍到黑屏）")
        print("Another PersonWatchdog instance is running. Stop it first, then retry --test-send.")
        return 3
    msg = text or "PersonWatchdog 测试通知"
    media = None
    try:
        idx = select_camera(cfg)
        cap = open_camera(idx)
        try:
            frame, brightness = grab_warmed_frame(cap, cfg)
            if frame is not None and brightness is not None:
                log.info("测试抓拍亮度: %.1f", brightness)
                if brightness >= float(cfg.get("min_frame_brightness", 8.0)):
                    faces = []
                    face_path = resolve_model_path(cfg) / cfg.get("face_model", "face_detection_yunet_2023mar.onnx")
                    if face_path.exists():
                        try:
                            faces = FaceDetector(face_path, cfg).detect(frame)
                            log.info("测试帧检测到 %d 张人脸", len(faces))
                        except Exception as exc:
                            log.warning("人脸检测不可用（不影响文字发送）: %s", exc)
                    media = save_snapshot(cfg, frame, [], faces)
                else:
                    log.warning(
                        "画面过黑（亮度 %.1f），测试消息不附照片：摄像头可能被占用（如 Windows 相机）、被遮挡或隐私开关关闭",
                        brightness,
                    )
        finally:
            cap.release()
    except Exception as exc:
        log.warning("测试快照获取失败，仅发送文字: %s", exc)
    sent = send_message(cfg, msg, media)
    if media and sent and not cfg.get("keep_snapshots", False):
        media.unlink(missing_ok=True)
        log.info("测试抓拍已删除: %s", media)
    return 0 if sent else 1


def cmd_reset_learning(cfg: dict) -> int:
    path = BASE_DIR / cfg.get("learning_data", "learning_data.json")
    lm = LearningMemory(path, cfg)
    lm.reset()
    print(f"learning data reset: {path} (threshold back to {cfg.get('conf_threshold', 0.35)})")
    log.info("学习数据已重置: %s", path)
    return 0


# ---------------------------------------------------------------------------
# 主循环
# ---------------------------------------------------------------------------

def resolve_model_path(cfg: dict) -> Path:
    models_dir = Path(cfg["models_dir"])
    if not models_dir.is_absolute():
        models_dir = BASE_DIR / models_dir
    return models_dir


def now_str() -> str:
    return _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def idle_detect_decision(
    motion: bool,
    now: float,
    last_detect_at: float,
    idle_detect_secs: float,
    in_confirm: bool,
    backoff_until: float,
) -> bool:
    """IDLE 状态是否运行检测：确认中始终活跃；有运动且不在空检冷却中；或定期扫描到期。"""
    if in_confirm:
        return True
    if motion and now >= backoff_until:
        return True
    return (now - last_detect_at) >= idle_detect_secs


def run(cfg: dict, duration=None, clock=None) -> int:
    models_dir = resolve_model_path(cfg)
    model_path = models_dir / cfg["model"]
    if not model_path.exists():
        log.error("模型不存在: %s —— 请先运行 setup.ps1 下载模型", model_path)
        return 2
    try:
        import onnxruntime as ort

        so = ort.SessionOptions()
        so.log_severity_level = 3
        so.intra_op_num_threads = max(1, int(cfg.get("onnx_threads", 4)))
        session = ort.InferenceSession(
            str(model_path), sess_options=so, providers=["CPUExecutionProvider"]
        )
    except Exception as exc:
        log.error("加载 ONNX 模型失败: %s", exc)
        return 2

    face_path = models_dir / cfg.get("face_model", "face_detection_yunet_2023mar.onnx")
    face_detector = None
    if not face_path.exists():
        log.warning("人脸模型不存在: %s —— 抓拍将退回人体框（请运行 setup.ps1 补齐）", face_path)

    learning = LearningMemory(BASE_DIR / cfg.get("learning_data", "learning_data.json"), cfg)
    sender = Sender(cfg)
    gate = MotionGate(
        width=cfg.get("motion_gate_width", 160),
        threshold=cfg.get("motion_threshold", 18.0),
        learn_rate=cfg.get("motion_learn_rate", 0.05),
    )
    tracker = PresenceTracker(cfg, clock=clock or time.monotonic)

    active_interval = max(0.05, float(cfg.get("active_interval_ms", 200)) / 1000.0)
    capture_interval = max(0.05, float(cfg.get("capture_interval_ms", 250)) / 1000.0)
    present_interval = max(0.2, float(cfg.get("present_interval_ms", 1000)) / 1000.0)
    idle_interval = max(0.05, float(cfg.get("idle_interval_ms", 500)) / 1000.0)
    idle_detect_secs = max(1.0, float(cfg.get("idle_detect_secs", 5.0)))
    idle_backoff_secs = max(0.5, float(cfg.get("idle_empty_backoff_secs", 2.0)))
    min_b = float(cfg.get("min_frame_brightness", 8.0))
    grace = float(cfg.get("grace_secs", 15))
    start = time.monotonic()
    cap = None
    last_motion_at = -10.0
    empty_backoff_until = 0.0
    last_detect_at = -1e9  # 布防后立即做一次扫描（静止的人也能被检出）

    log.info(
        "%s v%s 启动 | 模型=%s | 人脸模型=%s | 目标=%s | 摄像头=index %s | 阈值=%.2f | 空闲扫描=%.0fs",
        APP_NAME, APP_VERSION, model_path.name, face_path.name, cfg["target"],
        cfg["camera_index"], learning.threshold, idle_detect_secs,
    )
    try:
        while True:
            try:
                if duration is not None and time.monotonic() - start >= duration:
                    log.info("达到测试时长（%.1f 秒），退出", duration)
                    break
                if cap is None or not cap.isOpened():
                    try:
                        idx = select_camera(cfg)
                        cap = open_camera(idx)
                        _, warm_b = grab_warmed_frame(cap, cfg)
                        log.info("摄像头已打开 index=%s（亮度 %s）", idx, f"{warm_b:.1f}" if warm_b is not None else "未知")
                        if warm_b is not None and warm_b < min_b:
                            log.warning(
                                "摄像头 index=%d 画面过黑（亮度 %.1f）：可能被其他应用占用（如 Windows 相机）、被遮挡或隐私开关关闭",
                                idx, warm_b,
                            )
                    except Exception as exc:
                        log.error("打开摄像头失败: %s（5 秒后重试）", exc)
                        time.sleep(5)
                        continue

                t0 = time.monotonic()
                ok, frame = cap.read()
                if not ok or frame is None:
                    log.error("摄像头读取失败，5 秒后重试")
                    cap.release()
                    cap = None
                    time.sleep(5)
                    continue

                now = time.monotonic()
                armed = (now - start) >= grace
                if not armed:
                    # 宽限期：只更新运动门控背景，不检测
                    gate.update(gate.downscale(frame))
                    time.sleep(idle_interval)
                    continue

                motion = gate.update(gate.downscale(frame))
                if motion:
                    last_motion_at = now
                state = tracker.state

                if state == tracker.CAPTURING:
                    run_detect = True
                elif state == tracker.PRESENT:
                    run_detect = True  # 仍需确认何时离开
                else:  # IDLE：运动（含空检冷却）、定期扫描（静止的人也能被检出）、或已在确认中
                    run_detect = idle_detect_decision(
                        motion, now, last_detect_at, idle_detect_secs, tracker.in_confirm, empty_backoff_until
                    )

                detections = []
                faces = []
                if run_detect:
                    last_detect_at = now
                    regions = learning.suppressed_regions(frame.shape)
                    detections = detect_people(
                        session, frame, cfg, conf=learning.threshold, suppress_regions=regions
                    )
                    present = bool(detections)
                    if (
                        not present
                        and tracker.state == tracker.IDLE
                        and not tracker.in_confirm
                    ):
                        # 运动但没检到人：进入冷却，避免持续空转 YOLO（省 CPU）
                        empty_backoff_until = now + idle_backoff_secs
                else:
                    present = False


                if state == tracker.CAPTURING and present:
                    if face_detector is None and face_path.exists():
                        face_detector = FaceDetector(face_path, cfg)
                    if face_detector is not None:
                        faces = face_detector.detect(frame)

                events = tracker.tick(present, frame, detections, faces)
                for ev in events:
                    if ev["type"] == "appear":
                        text = (cfg.get("appear_template") or cfg["message_template"]).format(time=now_str())
                        media = None
                        best_frame = ev.get("frame")
                        if best_frame is not None and cfg.get("send_snapshot", True):
                            if frame_brightness(best_frame) >= min_b:
                                media = save_snapshot(cfg, best_frame, ev.get("detections"), ev.get("faces"))
                            else:
                                log.warning("最佳帧过黑（亮度 %.1f），本次通知不附照片", frame_brightness(best_frame))
                        sender.send(text, media)
                        log.info(
                            "事件[出现] 人脸=%s 检测框=%d 附照片=%s",
                            ev.get("had_face"), len(ev.get("detections") or []), bool(media),
                        )
                    elif ev["type"] == "leave":
                        duration = float(ev.get("duration", 0.0))
                        if cfg.get("notify_on_leave", True):
                            text = cfg["leave_template"].format(duration=format_duration(duration))
                            sender.send(text, None)
                        best_frame = ev.get("frame")
                        shape = best_frame.shape if best_frame is not None else None
                        learning.learn_from_event(ev, ev.get("detections"), shape)
                        log.info(
                            "事件[离开] 停留 %.1f 秒 | 学习阈值=%.2f | 抑制区域=%d",
                            duration, learning.threshold, len(learning.suppressed_regions(frame.shape)),
                        )

                elapsed = time.monotonic() - t0
                if state == tracker.CAPTURING:
                    interval = capture_interval
                elif state == tracker.PRESENT:
                    interval = present_interval
                elif state == tracker.IDLE and run_detect:
                    interval = active_interval
                else:
                    interval = idle_interval
                time.sleep(max(0.0, interval - elapsed))
            except KeyboardInterrupt:
                raise
            except Exception:
                log.exception("主循环异常，5 秒后重新打开摄像头并继续")
                try:
                    if cap is not None:
                        cap.release()
                except Exception:
                    pass
                cap = None
                time.sleep(5)
    except KeyboardInterrupt:
        log.info("收到中断，退出")
    finally:
        if cap is not None:
            cap.release()
        if not sender.close(60):
            log.warning("退出时发送队列未完全排空（可能有消息未送达）")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog=APP_NAME, description="检测摄像头前经过的人，并通过 Hermes 发送飞书通知（文字 + 清晰抓拍）"
    )
    parser.add_argument("--config", default=str(BASE_DIR / "config.json"), help="配置文件路径")
    parser.add_argument("--list-cameras", action="store_true", help="枚举可用摄像头并退出")
    parser.add_argument(
        "--test-send",
        nargs="?",
        const="PersonWatchdog 测试通知",
        metavar="TEXT",
        help="发送一条测试通知（文字+抓拍）后退出",
    )
    parser.add_argument("--reset-learning", action="store_true", help="清空学习数据并恢复默认阈值")
    parser.add_argument("--duration", type=float, default=None, help="运行 N 秒后自动退出（测试用）")
    parser.add_argument("--version", action="version", version=f"{APP_NAME} {APP_VERSION}")
    args = parser.parse_args(argv)

    setup_logging()
    cfg = load_config(Path(args.config))
    if not Path(args.config).exists():
        Path(args.config).write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
        log.info("已生成默认配置文件: %s", args.config)

    if args.list_cameras:
        try:
            cams = list_cameras()
        except Exception as exc:
            log.error("枚举摄像头失败: %s（请先运行 setup.ps1 安装依赖）", exc)
            return 2
        if not cams:
            log.error("未找到可用摄像头")
            return 1
        names = list_device_names()
        for idx, brightness, w, h in cams:
            b = "unavailable" if brightness is None else f"{brightness:.1f}"
            nm = f"  {names[idx]}" if names and idx < len(names) else ""
            print(f"camera index={idx}  {w}x{h}  brightness={b}{nm}")
        print("Note: watchdog prefers the physical camera by name and excludes OBS/OMEN virtual devices.")
        return 0

    if args.reset_learning:
        return cmd_reset_learning(cfg)

    if args.test_send is not None:
        return cmd_test_send(cfg, args.test_send)

    if not acquire_single_instance():
        log.error("已有 PersonWatchdog 实例在运行（摄像头被占用）。请先停止旧实例（任务管理器结束 pythonw.exe）再启动。")
        print("Another PersonWatchdog instance is already running. Stop it first (see logs/watchdog.log).")
        return 3

    return run(cfg, duration=args.duration)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)