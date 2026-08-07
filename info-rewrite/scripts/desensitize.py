#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""数据脱敏 / 恢复工具（过程脱敏 + 交付恢复）。

用法:
  mask:
    python desensitize.py mask -i 原文.txt -o 脱敏.txt -m 映射.json [--names 名单.txt]
  restore:
    python desensitize.py restore -i 脱敏.txt -m 映射.json -o 恢复.txt

占位符格式：【类型序号】，如 【姓名A】、【手机1】、【证件1】、【微信1】。
mask 与 restore 往返一致：restore(mask(text)) == text。
人名走名单（一行一个，按最长优先精确子串匹配）；手机/证件/座机/邮箱/微信走正则。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

PH = re.compile(r"【[^】]+?】")


def build_patterns(names: list[str]) -> list[tuple[re.Pattern, str, int]]:
    """返回 [(编译后正则, 类型, 要替换的组号)]。组号 0=整段替换；微信用组 1 保留前缀。"""
    pats: list[tuple[re.Pattern, str, int]] = []
    for n in sorted((x.strip() for x in names if x.strip()), key=len, reverse=True):
        pats.append((re.compile(re.escape(n)), "姓名", 0))
    pats += [
        (re.compile(r"1[3-9]\d{9}"), "手机", 0),
        (re.compile(r"\d{17}[\dXx]"), "证件", 0),
        (re.compile(r"0\d{2,3}-?\d{7,8}"), "座机", 0),
        (re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+"), "邮箱", 0),
        (re.compile(r"(?:微信号|微信|wx|weixin)\s*[:：]?\s*([A-Za-z][\w-]{5,19})"), "微信", 1),
    ]
    return pats


def _letter_seq(i: int) -> str:
    s = ""
    while True:
        s = chr(ord("A") + (i % 26)) + s
        i = i // 26 - 1
        if i < 0:
            return s


def mask_text(text: str, names: list[str]) -> tuple[str, dict[str, str]]:
    """返回 (脱敏文本, 映射{原文片段 -> 占位符})。"""
    mapping: dict[str, str] = {}
    counts: dict[str, int] = {}

    for pat, typ, grp in build_patterns(names):
        def repl(m, typ=typ, grp=grp):
            raw = m.group(grp)
            ph = mapping.get(raw)
            if ph is None:
                counts[typ] = counts.get(typ, 0) + 1
                ph = "【%s%s】" % (typ, _letter_seq(counts[typ] - 1)) if typ == "姓名" else "【%s%d】" % (typ, counts[typ])
                mapping[raw] = ph
            if grp == 0:
                return ph
            return m.group(0)[: m.start(grp) - m.start(0)] + ph
        text = pat.sub(repl, text)
    return text, mapping


def restore_text(text: str, mapping: dict[str, str]) -> str:
    rev = {ph: raw for raw, ph in mapping.items()}

    def repl(m):
        return rev.get(m.group(0), m.group(0))

    return PH.sub(repl, text)


def _read_names(path: str | None) -> list[str]:
    if not path:
        return []
    return [ln.strip() for ln in Path(path).read_text(encoding="utf-8").splitlines() if ln.strip()]


def main() -> int:
    ap = argparse.ArgumentParser(description="数据脱敏/恢复工具")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_mask = sub.add_parser("mask", help="打码")
    p_mask.add_argument("-i", "--input", required=True)
    p_mask.add_argument("-o", "--output", required=True)
    p_mask.add_argument("-m", "--mapping", required=True, help="映射 JSON 输出路径")
    p_mask.add_argument("--names", default="", help="人名名单文件，一行一个")

    p_res = sub.add_parser("restore", help="恢复")
    p_res.add_argument("-i", "--input", required=True)
    p_res.add_argument("-m", "--mapping", required=True, help="映射 JSON 输入路径")
    p_res.add_argument("-o", "--output", required=True)

    args = ap.parse_args()
    text = Path(args.input).read_text(encoding="utf-8")

    if args.cmd == "mask":
        masked, mapping = mask_text(text, _read_names(args.names))
        Path(args.output).write_text(masked, encoding="utf-8")
        Path(args.mapping).write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8")
        print("masked=%d chars, placeholders=%d -> %s" % (len(masked), len(mapping), args.output))
    else:
        mapping = json.loads(Path(args.mapping).read_text(encoding="utf-8"))
        restored = restore_text(text, mapping)
        Path(args.output).write_text(restored, encoding="utf-8")
        print("restored=%d chars -> %s" % (len(restored), args.output))
    return 0


if __name__ == "__main__":
    sys.exit(main())