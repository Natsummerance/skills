#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate the fixed github-promo-post -> xhs-publish artifact contract."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from PIL import Image

REQUIRED = ("title", "body", "topics", "images", "source_urls", "version_state")
IMAGE_NAMES = (
    "xhs-01-cover.jpg", "xhs-02-pain.jpg", "xhs-03-fast.jpg",
    "xhs-04-fix.jpg", "xhs-05-convert.jpg", "xhs-06-cta.jpg",
)
BANNED = ("公众号", "微信", "闲鱼", "咸鱼", "转卖", "出票", "转让", "售票", "二维码", "淘口令", "淘宝")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifacts", type=Path)
    args = parser.parse_args()
    root = args.artifacts.resolve()
    errors: list[str] = []
    try:
        metadata = json.loads((root / "metadata.json").read_text(encoding="utf-8"))
    except Exception as exc:
        print(json.dumps({"ok": False, "errors": [f"metadata.json 无法读取: {exc}"]}, ensure_ascii=False))
        return 1
    for key in REQUIRED:
        if not metadata.get(key):
            errors.append(f"metadata 缺少 {key}")
    title = str(metadata.get("title", "")).strip()
    body = str(metadata.get("body", "")).strip()
    topics = metadata.get("topics", [])
    if len(title) > 20: errors.append("标题超过 20 字")
    if not 600 <= len(body) <= 900: errors.append("正文必须为 600–900 字")
    if re.search(r"https?://|www\\.", body, re.I): errors.append("正文含真实 URL")
    if bad := [word for word in BANNED if word.lower() in (title + body).lower()]: errors.append("命中敏感词: " + ", ".join(bad))
    if not isinstance(topics, list) or len(topics) != 5 or any(not str(x).strip() or str(x).startswith("#") for x in topics):
        errors.append("topics 必须是 5 个不带 # 的话题")
    image_paths = metadata.get("images", [])
    if not isinstance(image_paths, list) or len(image_paths) != 6:
        errors.append("images 必须为 6 张")
        image_paths = []
    for index, raw in enumerate(image_paths):
        path = Path(raw)
        if path.name != IMAGE_NAMES[index]: errors.append(f"图片命名或顺序错误: {path.name}")
        if not path.is_file():
            errors.append(f"图片不存在: {path}")
            continue
        try:
            if Image.open(path).size != (1080, 1440): errors.append(f"图片尺寸错误: {path.name}")
        except Exception as exc:
            errors.append(f"图片无法读取: {path.name}: {exc}")
    for filename, value in (("title.txt", title), ("body.txt", body), ("topics.txt", "\n".join(map(str, topics)))):
        path = root / filename
        if not path.is_file(): errors.append(f"缺少 {filename}")
        elif not path.read_text(encoding="utf-8").strip(): errors.append(f"{filename} 为空")
    state = str(metadata.get("version_state", ""))
    if state != "release" and ("已发布" in body or "正式发布" in body):
        errors.append("非正式 Release 不得写已发布")
    print(json.dumps({"ok": not errors, "errors": errors, "images": image_paths}, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
