#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
poster 卡严格校验器 — 像素级范式校验（与视觉复核互补，语义问题交 vision_analyze）。

用法:
    python validate_poster.py <img.png> [img2.png ...]
    python validate_poster.py <dir>            # 校验目录下所有 png
    python validate_poster.py <img> --json     # 机器可读输出
    python validate_poster.py <img> --thresholds coverage=0.22,blank_band=120,bottom_gap=90

校验项（阈值见 SPEC / 可 --thresholds 覆盖）:
    size          尺寸必须 1080×1440
    edge_clean    四边 4px 带内内容像素占比 < 2%      （防白边 / 截图边缘残留）
    coverage      内容像素占比 ≥ 22%                 （防整卡太空）
    blank_band    最大连续空白行带 ≤ 120px           （防「中间大面积空白」，核心项）
    bottom_gap    最底内容像素距画布底 ≤ 90px        （防底部截断 / 悬空）
    top_gap       最顶内容像素距画布顶 ≤ 220px       （防头部空荡）
    side_clear    左右 8px 带内内容像素占比 < 1%     （防出血 / 元素贴边）

背景判定：四角 12×12 平均色为基准；像素与基准欧氏距离 > 40 视为「内容像素」。
装饰层（noise/grid/半透明水印）对比度低，自动归为背景，不影响判定。

退出码：0=全部 PASS，1=存在 FAIL（供生成器/CI 联动）。
"""
import argparse
import json
import sys
from pathlib import Path

from PIL import Image

TARGET_W, TARGET_H = 1080, 1440
DEFAULT_THRESHOLDS = {
    "edge_content": 0.02,     # 边缘带内容像素占比上限
    "coverage": 0.05,         # 内容像素占比下限（深色底海报实测 6-13%，5%=防整卡空）
    "blank_band": 120,        # 最大空白行带上限 px（≈8.3% 高）
    "bottom_gap": 90,         # 底部内容距底上限 px
    "top_gap": 220,           # 顶部内容距顶上限 px
    "side_content": 0.01,     # 左右带内容像素占比上限
    "bg_dist": 40,            # 与背景色判定距离
    "band_row_ratio": 0.005,  # 空白行 = 内容像素 < 行宽×该比例
}
EDGE_BAND = 4   # 四边检测带宽度
SIDE_BAND = 8   # 左右检测带宽度


def _bg_color(im):
    w, h = im.size
    px = im.load()
    samples = []
    for x in range(12):
        for y in range(12):
            samples.append(px[x, y])
            samples.append(px[w - 1 - x, y])
            samples.append(px[x, h - 1 - y])
            samples.append(px[w - 1 - x, h - 1 - y])
    n = len(samples)
    return tuple(sum(c[i] for c in samples) // n for i in range(3))


def _is_content(px, bg, dist2):
    dr, dg, db = px[0] - bg[0], px[1] - bg[1], px[2] - bg[2]
    return dr * dr + dg * dg + db * db > dist2


def validate(path, thresholds=None):
    t = {**DEFAULT_THRESHOLDS, **(thresholds or {})}
    im = Image.open(path).convert("RGB")
    w, h = im.size
    px = im.load()
    bg = _bg_color(im)
    dist2 = t["bg_dist"] ** 2

    results = {}

    # 1) size
    results["size"] = (w == TARGET_W and h == TARGET_H,
                       f"{w}×{h}")

    # 内容像素矩阵 + 行/列统计
    row_content = [0] * h
    col_content = [0] * w
    total = 0
    for y in range(h):
        for x in range(w):
            if _is_content(px[x, y], bg, dist2):
                row_content[y] += 1
                col_content[x] += 1
                total += 1

    # 2) edge_clean：四边 4px 带
    edge_cnt = 0
    edge_total = 0
    for y in range(EDGE_BAND):
        for x in range(w):
            edge_total += 1
            if _is_content(px[x, y], bg, dist2):
                edge_cnt += 1
            if _is_content(px[x, h - 1 - y], bg, dist2):
                edge_cnt += 1
    for x in range(EDGE_BAND):
        for y in range(EDGE_BAND, h - EDGE_BAND):
            edge_total += 1
            if _is_content(px[x, y], bg, dist2):
                edge_cnt += 1
            if _is_content(px[w - 1 - x, y], bg, dist2):
                edge_cnt += 1
    edge_ratio = edge_cnt / edge_total
    results["edge_clean"] = (edge_ratio < t["edge_content"],
                             f"边缘内容 {edge_ratio:.2%}")

    # 3) coverage
    cov = total / (w * h)
    results["coverage"] = (cov >= t["coverage"], f"内容占比 {cov:.1%}")

    # 4) blank_band：最大连续空白行带
    band_thr = int(w * t["band_row_ratio"])
    max_band = cur = 0
    for y in range(h):
        if row_content[y] < band_thr:
            cur += 1
            max_band = max(max_band, cur)
        else:
            cur = 0
    results["blank_band"] = (max_band <= t["blank_band"],
                             f"最大空白带 {max_band}px")

    # 5) bottom_gap / 6) top_gap
    ys = [y for y in range(h) if row_content[y] >= band_thr]
    if ys:
        bottom_gap = h - 1 - max(ys)
        top_gap = min(ys)
        results["bottom_gap"] = (bottom_gap <= t["bottom_gap"],
                                 f"底部距内容 {bottom_gap}px")
        results["top_gap"] = (top_gap <= t["top_gap"],
                              f"顶部距内容 {top_gap}px")
    else:
        results["bottom_gap"] = (False, "整卡无内容")
        results["top_gap"] = (False, "整卡无内容")

    # 7) side_clear：左右 8px 带
    side_cnt = sum(col_content[x] for x in range(SIDE_BAND)) + \
        sum(col_content[w - 1 - x] for x in range(SIDE_BAND))
    side_ratio = side_cnt / (2 * SIDE_BAND * h)
    results["side_clear"] = (side_ratio < t["side_content"],
                             f"左右带内容 {side_ratio:.2%}")

    ok = all(v[0] for v in results.values())
    return ok, results, bg


def main():
    ap = argparse.ArgumentParser(description="poster 卡像素级范式校验")
    ap.add_argument("paths", nargs="+", help="PNG/JPG 文件或目录")
    ap.add_argument("--json", action="store_true", help="JSON 输出")
    ap.add_argument("--thresholds", default="",
                    help="覆盖阈值,逗号分隔 key=value, 如 coverage=0.25,blank_band=100")
    args = ap.parse_args()

    thr = {}
    for kv in args.thresholds.split(","):
        if kv.strip():
            k, v = kv.split("=")
            thr[k.strip()] = float(v.strip())

    files = []
    for p in args.paths:
        p = Path(p)
        if p.is_dir():
            files += [f for f in sorted(p.iterdir()) if f.suffix.lower() in {".png", ".jpg", ".jpeg"} and not f.name.startswith("_")]
        else:
            if p.name.startswith("_"):
                print(f"[skip] {p.name} (中间产物)")
                continue
            files.append(p)

    report = []
    all_ok = True
    for f in files:
        try:
            ok, results, bg = validate(f, thr)
        except Exception as e:
            ok, results, bg = False, {"error": (False, str(e))}, (0, 0, 0)
        all_ok = all_ok and ok
        report.append({"file": str(f), "pass": ok, "checks": results})
        if not args.json:
            flag = "✅ PASS" if ok else "❌ FAIL"
            print(f"[{flag}] {f.name}  (bg=#{bg[0]:02X}{bg[1]:02X}{bg[2]:02X})")
            for k, (passed, msg) in results.items():
                print(f"    {'✓' if passed else '✗'} {k:12s} {msg}")

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=1))
    else:
        npass = sum(1 for r in report if r["pass"])
        print(f"\n汇总: {npass}/{len(report)} 通过")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
