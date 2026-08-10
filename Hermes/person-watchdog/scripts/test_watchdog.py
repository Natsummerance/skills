# -*- coding: utf-8 -*-
"""PersonWatchdog v2 单元测试（TDD）。
运行：.venv\\Scripts\\python.exe -m unittest test_watchdog -v
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import cv2
import numpy as np

import watchdog as wd


class FakeClock:
    def __init__(self, t=0.0):
        self.t = t

    def __call__(self):
        return self.t

    def advance(self, dt):
        self.t += dt


def cfg_with(**kw):
    cfg = dict(wd.DEFAULT_CONFIG)
    cfg.update(kw)
    return cfg


class FormatDurationTests(unittest.TestCase):
    def test_zero(self):
        self.assertEqual(wd.format_duration(0), "0 秒")

    def test_seconds_only(self):
        self.assertEqual(wd.format_duration(30), "30 秒")

    def test_minutes_and_seconds(self):
        self.assertEqual(wd.format_duration(65), "1 分 5 秒")

    def test_hours(self):
        self.assertEqual(wd.format_duration(3725), "1 小时 2 分 5 秒")


class MotionGateTests(unittest.TestCase):
    def _frame(self, value):
        return np.full((90, 160), value, dtype=np.uint8)

    def _gate(self):
        return wd.MotionGate(width=160, threshold=18.0, learn_rate=0.05)

    def test_first_frame_no_motion(self):
        g = self._gate()
        self.assertFalse(g.update(self._frame(100)))

    def test_identical_frames_no_motion(self):
        g = self._gate()
        g.update(self._frame(100))
        self.assertFalse(g.update(self._frame(100)))
        self.assertFalse(g.update(self._frame(100)))

    def test_change_detected(self):
        g = self._gate()
        g.update(self._frame(100))
        self.assertTrue(g.update(self._frame(160)))

    def test_small_change_below_threshold_ignored(self):
        g = self._gate()
        g.update(self._frame(100))
        self.assertFalse(g.update(self._frame(110)))

    def test_background_adapts_to_lighting(self):
        g = self._gate()
        g.update(self._frame(100))
        self.assertTrue(g.update(self._frame(160)))
        motion_after = False
        for _ in range(250):
            motion_after = g.update(self._frame(160))
        self.assertFalse(motion_after)

    def test_reset(self):
        g = self._gate()
        g.update(self._frame(100))
        g.update(self._frame(160))
        g.reset()
        self.assertFalse(g.update(self._frame(100)))


class PresenceTrackerTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.cfg = cfg_with(
            grace_secs=15,
            human_confirm_frames=3,
            capture_window_secs=6,
            exit_confirm_secs=5,
        )

    def _tracker(self):
        return wd.PresenceTracker(self.cfg, clock=self.clock)

    def _frame(self):
        return np.zeros((64, 64, 3), dtype=np.uint8)

    def _det(self):
        return [(10, 10, 50, 50, 0.9)]

    def _faces(self):
        return [(20, 20, 40, 40, 0.9)]

    def _confirm(self, tr):
        for _ in range(3):
            self.clock.advance(0.2)
            self.assertEqual(tr.tick(True, self._frame(), self._det(), self._faces()), [])

    def _capture_until_appear(self, tr):
        while True:
            self.clock.advance(0.2)
            evs = tr.tick(True, self._frame(), self._det(), self._faces())
            if evs:
                return evs

    def test_grace_ignores_person(self):
        tr = self._tracker()
        for _ in range(20):
            self.clock.advance(0.2)
            self.assertEqual(tr.tick(True, self._frame(), self._det(), self._faces()), [])
        self.assertFalse(tr.armed())

    def test_appear_after_confirm_and_capture_window(self):
        tr = self._tracker()
        self.clock.advance(15.5)
        self._confirm(tr)
        self.assertEqual(tr.state, "CAPTURING")
        evs = self._capture_until_appear(tr)
        self.assertEqual(len(evs), 1)
        self.assertEqual(evs[0]["type"], "appear")
        self.assertIsNotNone(evs[0].get("frame"))
        self.assertTrue(evs[0]["had_face"])
        self.assertEqual(tr.state, "PRESENT")

    def test_no_duplicate_appear_while_present(self):
        tr = self._tracker()
        self.clock.advance(15.5)
        self._confirm(tr)
        self._capture_until_appear(tr)
        for _ in range(30):
            self.clock.advance(0.2)
            self.assertEqual(tr.tick(True, self._frame(), self._det(), self._faces()), [])

    def test_leave_emits_duration(self):
        tr = self._tracker()
        self.clock.advance(15.5)
        self._confirm(tr)          # appear_time = 16.1, capture_until = 22.1
        self._capture_until_appear(tr)  # appear at 22.1
        evs = tr.tick(False)       # absent_since = 22.1
        self.assertEqual(evs, [])
        for _ in range(5):
            self.clock.advance(1.0)
            evs = tr.tick(False)
            if evs:
                break
        self.assertEqual(len(evs), 1)
        self.assertEqual(evs[0]["type"], "leave")
        self.assertAlmostEqual(evs[0]["duration"], 11.0, delta=0.2)
        self.assertEqual(tr.state, "IDLE")

    def test_ream_after_leave(self):
        tr = self._tracker()
        self.clock.advance(15.5)
        self._confirm(tr)
        self._capture_until_appear(tr)
        for _ in range(6):
            self.clock.advance(1.0)
            tr.tick(False)
        self.assertEqual(tr.state, "IDLE")
        # second appearance
        self._confirm(tr)
        evs = self._capture_until_appear(tr)
        self.assertEqual(len(evs), 1)
        self.assertEqual(evs[0]["type"], "appear")

    def test_leave_during_capture_emits_both(self):
        tr = self._tracker()
        self.clock.advance(15.5)
        self._confirm(tr)          # appear_time = 16.1, capture_until = 22.1
        self.clock.advance(0.2)
        tr.tick(True, self._frame(), self._det(), self._faces())  # one capture frame
        evs = tr.tick(False)       # absent_since = 16.5
        self.assertEqual(evs, [])
        for _ in range(5):
            self.clock.advance(1.0)
            evs = tr.tick(False)
            if evs:
                break
        self.assertEqual([e["type"] for e in evs], ["appear", "leave"])
        self.assertAlmostEqual(evs[1]["duration"], 5.0, delta=0.2)

    def test_in_confirm_flag(self):
        tr = self._tracker()
        self.clock.advance(15.5)
        self.assertFalse(tr.in_confirm)
        tr.tick(True, self._frame(), self._det(), self._faces())
        self.assertTrue(tr.in_confirm)
        tr.tick(False)
        self.assertFalse(tr.in_confirm)

    def test_absent_during_confirm_resets(self):
        tr = self._tracker()
        self.clock.advance(15.5)
        tr.tick(True, self._frame(), self._det(), self._faces())
        tr.tick(True, self._frame(), self._det(), self._faces())
        tr.tick(False)
        self.assertEqual(tr.state, "IDLE")
        self.clock.advance(0.2)
        tr.tick(True, self._frame(), self._det(), self._faces())
        self.assertEqual(tr.state, "IDLE")  # still needs 3 consecutive


class BestShotTests(unittest.TestCase):
    def setUp(self):
        self.cfg = cfg_with(min_face_ratio=0.06, clarity_norm_k=1000.0)

    def _noise(self, size=128):
        rng = np.random.default_rng(42)
        return (rng.random((size, size, 3)) * 255).astype(np.uint8)

    def test_clear_face_beats_blurry_small_face(self):
        sharp = self._noise()
        blur = cv2.GaussianBlur(sharp, (31, 31), 0)
        faces_sharp = [(20, 20, 100, 100, 0.9)]   # 大且清晰
        faces_blur = [(48, 48, 86, 86, 0.6)]      # 小且模糊
        s_sharp = wd.best_shot_score(sharp, [], faces_sharp, self.cfg)[0]
        s_blur = wd.best_shot_score(blur, [], faces_blur, self.cfg)[0]
        self.assertGreater(s_sharp, s_blur)

    def test_fallback_uses_body_ratio_when_no_face(self):
        sharp = self._noise()
        score, _ = wd.best_shot_score(sharp, [(10, 10, 110, 110, 0.9)], [], self.cfg)
        self.assertGreater(score, 0.0)

    def test_face_preferred_over_blurry_body(self):
        sharp = self._noise()
        blur = cv2.GaussianBlur(sharp, (51, 51), 0)
        s_face = wd.best_shot_score(sharp, [], [(30, 30, 90, 90, 0.9)], self.cfg)[0]
        s_body = wd.best_shot_score(blur, [(5, 5, 120, 120, 0.9)], [], self.cfg)[0]
        self.assertGreater(s_face, s_body)

    def test_bestshot_keeps_highest_score_frame(self):
        bs = wd.BestShot(self.cfg)
        blur = cv2.GaussianBlur(self._noise(), (31, 31), 0)
        bs.push(blur, [], [(30, 30, 90, 90, 0.9)])
        sharp = self._noise()
        bs.push(sharp, [], [(30, 30, 90, 90, 0.9)])
        best = bs.best()
        self.assertIsNotNone(best)
        self.assertTrue(np.array_equal(best[0], sharp))
        self.assertTrue(bs.has_face)


class LearningMemoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "learning_data.json"
        self.cfg = cfg_with(
            conf_threshold=0.35,
            adaptive_threshold_min=0.25,
            adaptive_threshold_max=0.55,
            adaptive_threshold_step=0.02,
            false_region_repeat=3,
            false_region_suppress_factor=0.4,
            false_alarm_max_secs=5.0,
            learning_grid=6,
        )

    def _lm(self):
        return wd.LearningMemory(self.path, self.cfg)

    def test_threshold_never_exceeds_max(self):
        lm = self._lm()
        for _ in range(50):
            lm.learn_from_event({"had_face": False, "duration": 1.0}, [], (100, 100, 3))
        self.assertLessEqual(lm.threshold, 0.55)

    def test_threshold_never_below_min(self):
        lm = self._lm()
        for _ in range(50):
            lm.learn_from_event({"had_face": True, "duration": 10.0}, [], (100, 100, 3))
        self.assertGreaterEqual(lm.threshold, 0.25)

    def test_threshold_steps_by_0_02(self):
        lm = self._lm()
        lm.learn_from_event({"had_face": False, "duration": 1.0}, [], (100, 100, 3))
        self.assertAlmostEqual(lm.threshold, 0.37)

    def test_false_region_suppressed_after_repeat(self):
        lm = self._lm()
        dets = [(10, 10, 50, 50, 0.9)]
        for _ in range(3):
            lm.learn_from_event({"had_face": False, "duration": 1.0}, dets, (200, 200, 3))
        key = lm.region_key(10, 10, 50, 50, 200, 200)
        self.assertTrue(lm.is_suppressed(key))
        self.assertAlmostEqual(lm.suppression_factor(key), 0.4)
        self.assertTrue(lm.suppressed_regions((200, 200)))

    def test_good_events_never_suppress(self):
        lm = self._lm()
        dets = [(10, 10, 50, 50, 0.9)]
        for _ in range(10):
            lm.learn_from_event({"had_face": True, "duration": 10.0}, dets, (200, 200, 3))
        self.assertEqual(lm.suppressed_regions((200, 200)), [])
        self.assertFalse(lm.is_suppressed(lm.region_key(10, 10, 50, 50, 200, 200)))

    def test_persistence_roundtrip(self):
        lm = self._lm()
        lm.learn_from_event({"had_face": False, "duration": 1.0}, [(10, 10, 50, 50, 0.9)], (200, 200, 3))
        lm.save()
        lm2 = self._lm()
        self.assertEqual(lm2.threshold, lm.threshold)
        self.assertEqual(lm2._data["regions"], lm._data["regions"])
        self.assertEqual(lm2._suppressed, lm._suppressed)

    def test_reset(self):
        lm = self._lm()
        lm.learn_from_event({"had_face": False, "duration": 1.0}, [(10, 10, 50, 50, 0.9)], (200, 200, 3))
        lm.reset()
        self.assertEqual(lm._data["regions"], {})
        self.assertEqual(lm.threshold, self.cfg["conf_threshold"])


class FaceDetectorTests(unittest.TestCase):
    def setUp(self):
        self.cfg = cfg_with(face_model="face_detection_yunet_2023mar.onnx", min_face_conf=0.6)
        self.model_path = BASE_DIR / "models" / self.cfg["face_model"]
        self.lena = BASE_DIR / "test_assets" / "lena.jpg"

    def test_lazy_load(self):
        fd = wd.FaceDetector(self.model_path, self.cfg)
        self.assertFalse(fd.is_loaded())

    def test_detects_lena_face(self):
        if not self.lena.exists():
            self.skipTest("缺少 test_assets/lena.jpg")
        fd = wd.FaceDetector(self.model_path, self.cfg)
        img = cv2.imread(str(self.lena))
        faces = fd.detect(img)
        self.assertGreaterEqual(len(faces), 1)

    def test_no_face_on_blank(self):
        fd = wd.FaceDetector(self.model_path, self.cfg)
        blank = np.full((240, 320, 3), 128, dtype=np.uint8)
        self.assertEqual(fd.detect(blank), [])


class YoloRegressionTests(unittest.TestCase):
    def test_bus_image_has_person(self):
        import onnxruntime as ort

        model = BASE_DIR / "models" / "yolo11m.onnx"
        bus = BASE_DIR / "test_assets" / "bus.jpg"
        if not model.exists() or not bus.exists():
            self.skipTest("缺少模型或测试图")
        so = ort.SessionOptions()
        so.log_severity_level = 3
        session = ort.InferenceSession(str(model), sess_options=so, providers=["CPUExecutionProvider"])
        img = cv2.imread(str(bus))
        dets = wd.detect_people(session, img, cfg_with(conf_threshold=0.35))
        self.assertGreaterEqual(len(dets), 1)


class SuppressionTests(unittest.TestCase):
    def test_suppress_detections_factor(self):
        dets = [(10, 10, 50, 50, 0.9), (100, 100, 150, 150, 0.9)]
        regions = [(0, 0, 60, 60)]
        out = wd.suppress_detections(dets, regions, 0.4)
        self.assertAlmostEqual(out[0][4], 0.36)
        self.assertEqual(out[1][4], 0.9)

    def test_no_regions_no_change(self):
        dets = [(10, 10, 50, 50, 0.9)]
        self.assertEqual(wd.suppress_detections(dets, [], 0.4), dets)


class SenderTests(unittest.TestCase):
    def test_create_no_window_constant(self):
        expected = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
        self.assertEqual(wd.CREATE_NO_WINDOW, expected)
        self.assertEqual(wd.CREATE_NO_WINDOW & 0x08000000, 0x08000000)

    def test_send_message_uses_creationflags(self):
        captured = {}

        def fake_run(cmd, **kw):
            captured["cmd"] = cmd
            captured.update(kw)
            return type("P", (), {"returncode": 0, "stdout": "ok", "stderr": ""})()

        orig_run = subprocess.run
        orig_resolve = wd.resolve_hermes
        subprocess.run = fake_run
        wd.resolve_hermes = lambda cfg: "hermes.exe"
        try:
            ok = wd.send_message(cfg_with(hermes_send="ignored.exe", target="feishu:test"), "hello")
        finally:
            subprocess.run = orig_run
            wd.resolve_hermes = orig_resolve
        self.assertTrue(ok)
        self.assertEqual(captured["creationflags"], wd.CREATE_NO_WINDOW)
        self.assertEqual(captured["cmd"][0], "hermes.exe")

    def test_sender_flush_and_media_delete(self):
        sent = []
        orig = wd.send_message

        def fake(cfg, text, media=None, timeout=90):
            sent.append((text, media))
            return True

        wd.send_message = fake
        try:
            with tempfile.TemporaryDirectory() as td:
                media = Path(td) / "shot.jpg"
                media.write_bytes(b"jpeg-data")
                cfg = cfg_with(keep_snapshots=False)
                s = wd.Sender(cfg)
                s.send("hello", media)
                s.send("world")
                ok = s.flush(timeout=10)
                s.close()
                self.assertTrue(ok)
                self.assertEqual(len(sent), 2)
                self.assertEqual(sent[0][0], "hello")
                self.assertEqual(sent[0][1], media)
                self.assertFalse(media.exists())
        finally:
            wd.send_message = orig

    def test_sender_keeps_media_on_failure(self):
        sent = []
        orig = wd.send_message

        def fake(cfg, text, media=None, timeout=90):
            sent.append((text, media))
            return False

        wd.send_message = fake
        try:
            with tempfile.TemporaryDirectory() as td:
                media = Path(td) / "shot.jpg"
                media.write_bytes(b"jpeg-data")
                s = wd.Sender(cfg_with(keep_snapshots=False))
                s.send("hello", media)
                ok = s.flush(timeout=10)
                s.close()
                self.assertTrue(ok)
                self.assertTrue(media.exists())
        finally:
            wd.send_message = orig


class ConfigTests(unittest.TestCase):
    def test_old_config_gets_v2_defaults(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "config.json"
            path.write_text(json.dumps({"camera_index": 1}), encoding="utf-8")
            cfg = wd.load_config(path)
        self.assertEqual(cfg["camera_index"], 1)
        self.assertEqual(cfg["human_confirm_frames"], 3)
        self.assertEqual(cfg["capture_window_secs"], 6)
        self.assertTrue(cfg["notify_on_leave"])
        self.assertEqual(cfg["face_model"], "face_detection_yunet_2023mar.onnx")
        self.assertEqual(cfg["idle_interval_ms"], 500)

class IdleDetectDecisionTests(unittest.TestCase):
    """IDLE 状态检测决策：运动触发、空检冷却、定期扫描、确认中保持活跃。"""

    def test_motion_without_backoff_triggers(self):
        self.assertTrue(wd.idle_detect_decision(True, now=10.0, last_detect_at=9.0,
                                                idle_detect_secs=5.0, in_confirm=False,
                                                backoff_until=0.0))

    def test_motion_in_backoff_is_suppressed(self):
        self.assertFalse(wd.idle_detect_decision(True, now=10.0, last_detect_at=9.0,
                                                 idle_detect_secs=5.0, in_confirm=False,
                                                 backoff_until=11.5))

    def test_motion_after_backoff_expires_triggers(self):
        self.assertTrue(wd.idle_detect_decision(True, now=12.0, last_detect_at=9.0,
                                                idle_detect_secs=5.0, in_confirm=False,
                                                backoff_until=11.5))

    def test_periodic_scan_without_motion_triggers(self):
        self.assertTrue(wd.idle_detect_decision(False, now=10.0, last_detect_at=4.0,
                                                idle_detect_secs=5.0, in_confirm=False,
                                                backoff_until=0.0))

    def test_no_motion_and_not_due_is_skipped(self):
        self.assertFalse(wd.idle_detect_decision(False, now=10.0, last_detect_at=9.0,
                                                 idle_detect_secs=5.0, in_confirm=False,
                                                 backoff_until=0.0))

    def test_confirm_in_progress_always_active(self):
        self.assertTrue(wd.idle_detect_decision(False, now=10.0, last_detect_at=9.9,
                                                idle_detect_secs=5.0, in_confirm=True,
                                                backoff_until=99.0))


class V22ConfigTests(unittest.TestCase):
    def test_new_interval_defaults_present(self):
        cfg = cfg_with()
        self.assertEqual(cfg["present_interval_ms"], 1000)
        self.assertEqual(cfg["capture_interval_ms"], 250)
        self.assertEqual(cfg["idle_empty_backoff_secs"], 2.0)
        self.assertEqual(cfg["onnx_threads"], 4)

    def test_old_config_gets_v22_defaults(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "config.json"
            path.write_text(json.dumps({"camera_index": 0}), encoding="utf-8")
            cfg = wd.load_config(path)
        self.assertEqual(cfg["present_interval_ms"], 1000)
        self.assertEqual(cfg["capture_interval_ms"], 250)
        self.assertEqual(cfg["idle_empty_backoff_secs"], 2.0)




if __name__ == "__main__":
    unittest.main(verbosity=2)
