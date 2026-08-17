#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prepare the signed-in default Edge profile for xhs_publish.

This intentionally never supplies --user-data-dir: publishing must use the
user's existing Edge login.  Restarting Edge is opt-in because it closes every
open Edge window; use it only after the user has asked to publish.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path


EDGE_CANDIDATES = (
    Path(r"C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe"),
    Path(r"C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe"),
)
DEFAULT_EDGE = next((path for path in EDGE_CANDIDATES if path.is_file()), EDGE_CANDIDATES[0])


def version(port: int) -> dict | None:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=1.5) as response:
            data = json.loads(response.read().decode("utf-8"))
        return data if "Edg/" in data.get("Browser", "") else None
    except Exception:
        return None


def wait_for_edge(port: int, seconds: int = 15) -> dict | None:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        found = version(port)
        if found:
            return found
        time.sleep(0.5)
    return None


def restart_edge(edge: Path, port: int) -> None:
    if not edge.is_file():
        raise RuntimeError(f"未找到 Edge: {edge}")
    # Edge background preloading can own the profile and silently discard CDP
    # arguments forwarded by a later process.  This is the verified recovery.
    subprocess.run(["taskkill", "/F", "/IM", "msedge.exe"], capture_output=True, text=True, check=False)
    time.sleep(1)
    subprocess.Popen(
        [str(edge), f"--remote-debugging-port={port}", "--remote-allow-origins=*"],
        creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
        close_fds=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="启动默认 Edge profile 的小红书 CDP 调试端口")
    parser.add_argument("--port", type=int, default=9222)
    parser.add_argument("--edge", type=Path, default=DEFAULT_EDGE)
    parser.add_argument("--restart-edge", action="store_true", help="关闭全部 Edge 后重启默认 profile（需用户已授权）")
    args = parser.parse_args()

    info = version(args.port)
    restarted = False
    if not info:
        if not args.restart_edge:
            print(json.dumps({
                "ready": False,
                "error": f"Edge CDP 未在 {args.port} 端口就绪；发布时加 --restart-edge 才会关闭并重启 Edge",
            }, ensure_ascii=False))
            return 1
        restart_edge(args.edge, args.port)
        restarted = True
        info = wait_for_edge(args.port)
    if not info:
        print(json.dumps({"ready": False, "error": "Edge 启动后 CDP 端口仍不可用"}, ensure_ascii=False))
        return 1
    print(json.dumps({
        "ready": True,
        "browser": info.get("Browser"),
        "debugPort": args.port,
        "restartedEdge": restarted,
        "profile": "default",
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
