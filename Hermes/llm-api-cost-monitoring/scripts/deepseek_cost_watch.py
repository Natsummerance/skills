#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DeepSeek 消耗监控（watchdog 模式，零 LLM token）。

每轮 cron 检查一次余额：
- 余额较上次下降（消耗）且自上次提醒累计满 1 元 -> 打印通知（cron 投递）
- 未满阈值 / 无变化 -> 静默退出（cron 不发送任何消息）
- 充值（余额上升）-> 重置累计

状态: HERMES_HOME/cron/deepseek_cost_state.json
用法: 由 Hermes cron 以 no_agent=True 调度；也可手动运行测试。
"""

import json
import os
import re
import sys
import time
import urllib.request
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERMES_HOME = Path(os.environ.get("HERMES_HOME") or str(Path.home() / ".hermes"))
STATE_FILE = HERMES_HOME / "cron" / "deepseek_cost_state.json"
ENV_FILE = HERMES_HOME / ".env"
BALANCE_URL = "https://api.deepseek.com/user/balance"
THRESHOLD = 1.0  # 通知阈值：元


def _load_env_key() -> str:
    """Fallback: 直接从 HERMES_HOME/.env 解析 DEEPSEEK_API_KEY（值不外泄）。"""
    try:
        text = ENV_FILE.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""
    m = re.search(r"^DEEPSEEK_API_KEY\s*=\s*[\"']?([^\"'\s]+)", text, re.M)
    return m.group(1) if m else ""


def get_balance(api_key: str) -> float:
    req = urllib.request.Request(
        BALANCE_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.loads(r.read().decode("utf-8"))
    total = 0.0
    for b in data.get("balance_infos", []):
        if b.get("currency") in ("CNY", "RMB", "cny"):
            total += float(b.get("total_balance", 0.0))
    return total


def _save(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    api_key = os.environ.get("DEEPSEEK_API_KEY", "").strip() or _load_env_key()
    if not api_key:
        print("⚠️ DeepSeek 消耗监控：找不到 DEEPSEEK_API_KEY（环境变量或 .env），请检查配置")
        return 1

    try:
        bal = get_balance(api_key)
    except Exception:
        # 网络/接口临时故障：静默退出，不打扰用户
        return 0

    state = {}
    if STATE_FILE.exists():
        try:
            state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            state = {}

    last = state.get("last_balance")
    acc = float(state.get("accrued", 0.0))
    now = time.strftime("%Y-%m-%d %H:%M")

    if last is None:
        # 首次运行：只记录基线，不发通知
        state.update({"last_balance": bal, "accrued": 0.0, "last_check": now, "notices": 0})
        _save(state)
        return 0

    delta = last - bal  # 正数 = 消耗；负数 = 充值
    if delta > 0:
        acc += delta
    elif delta < 0:
        acc = 0.0  # 充值，重置提醒周期

    state["last_balance"] = bal
    state["accrued"] = acc
    state["last_check"] = now

    if acc >= THRESHOLD:
        state["accrued"] = 0.0
        state["notices"] = int(state.get("notices", 0)) + 1
        _save(state)
        print(f"💰 DeepSeek 消耗提醒：自上次提醒以来已消耗 ¥{acc:.2f}，当前余额 ¥{bal:.2f}")
        return 0

    _save(state)
    return 0


if __name__ == "__main__":
    sys.exit(main())
