#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""机械校验：原文 vs 改写稿。

用法:
  python verify_rewrite.py 原文.txt 改写稿.txt \
      [--forbidden "你(?!们)" "我妈" "你妈"] \
      [--count-allowed "你们:1" "他妈妈:4"] \
      [--report 校验报告.md]

输出：词频统计、残留词扫描（含行号与上下文）、逐句 diff 摘要、通过/失败结论。
退出码：0=通过；1=存在残留或计数不符。
"""
from __future__ import annotations

import argparse
import difflib
import re
import sys
from pathlib import Path

# 控制台输出统一 UTF-8，避免 GBK 报错
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def load(p: str) -> str:
    return Path(p).read_text(encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="改写稿机械校验")
    ap.add_argument("original", help="原文路径")
    ap.add_argument("draft", help="改写稿路径")
    ap.add_argument("--forbidden", nargs="*", default=[], help="禁止出现的正则/词形")
    ap.add_argument("--count-allowed", nargs="*", default=[], help="期望计数，格式 词:数量")
    ap.add_argument("--report", default="", help="校验报告 Markdown 输出路径")
    args = ap.parse_args()

    orig = load(args.original)
    draft = load(args.draft)
    lines = draft.splitlines()

    # 词频统计
    stats = {}
    for tok in ["你", "你们", "他", "她", "妈妈", "他妈妈", "爸爸", "爸妈"]:
        stats[tok] = len(re.findall(re.escape(tok), draft))

    # 残留词扫描
    residual = []
    for f in args.forbidden:
        try:
            rx = re.compile(f)
        except re.error:
            rx = re.compile(re.escape(f))
        for i, ln in enumerate(lines, 1):
            for m in rx.finditer(ln):
                s = max(0, m.start() - 8)
                e = min(len(ln), m.end() + 8)
                residual.append((i, f, ln[s:e]))

    # 计数核对
    mismatch = []
    for item in args.count_allowed:
        if ":" not in item:
            continue
        tok, want_s = item.rsplit(":", 1)
        try:
            want = int(want_s)
        except ValueError:
            continue
        got = len(re.findall(re.escape(tok), draft))
        if got != want:
            mismatch.append((tok, want, got))

    # 逐句 diff 摘要
    ol, dl = orig.splitlines(), draft.splitlines()
    diff = list(difflib.unified_diff(ol, dl, fromfile="original", tofile="draft", lineterm="", n=0))
    changed = sum(1 for d in diff if (d.startswith("+") or d.startswith("-")) and not d.startswith(("+++", "---")))

    ok = (not residual) and (not mismatch)

    lines_out = [
        "# 改写机械校验报告",
        "",
        "- 原文：%s（%d 字符）" % (args.original, len(orig)),
        "- 改写稿：%s（%d 字符）" % (args.draft, len(draft)),
        "- 结论：%s" % ("通过" if ok else "不通过"),
        "",
        "## 词频统计",
        "",
        "| 词形 | 次数 |",
        "|---|---|",
    ]
    for tok, n in stats.items():
        lines_out.append("| %s | %d |" % (tok, n))
    lines_out += ["", "## 残留词扫描", ""]
    if residual:
        lines_out.append("发现 %d 处残留：" % len(residual))
        lines_out.append("")
        lines_out.append("| 行 | 规则 | 上下文 |")
        lines_out.append("|---|---|---|")
        for i, f, ctx in residual:
            lines_out.append("| %d | `%s` | %s |" % (i, f, ctx))
    else:
        lines_out.append("无残留。")
    lines_out += ["", "## 计数核对", ""]
    if mismatch:
        lines_out.append("| 词形 | 期望 | 实际 |")
        lines_out.append("|---|---|---|")
        for tok, want, got in mismatch:
            lines_out.append("| %s | %d | %d |" % (tok, want, got))
    else:
        lines_out.append("全部符合期望。")
    lines_out += ["", "## 逐句 diff 摘要", ""]
    lines_out.append("有改动的行数：%d" % changed)
    if diff:
        lines_out.append("")
        lines_out.append("```diff")
        lines_out.extend(diff)
        lines_out.append("```")

    report = "\n".join(lines_out) + "\n"
    if args.report:
        Path(args.report).write_text(report, encoding="utf-8")
    print(report)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())