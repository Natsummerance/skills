# -*- coding: utf-8 -*-
"""enrich_stills.py — 从 TMDB 搜索并下载电影高清剧照，可选直接追加到已发布小红书笔记。

流程（已实测跑通，2026-08-07）：
1. 用 TMDB 电影页（https://www.themoviedb.org/movie/<id>）解析图片页 slug；
2. 抓 backdrops 页并按社区评分排序（?image_sort=rating.desc），解析每张原图路径与分辨率；
3. 按最小宽度过滤、取评分最高的前 N 张，下载 original 原图到 out-dir；
4. 若给 --note-id，自动调用 xhs_publish.py update 的“仅配图”模式（不改标题/正文）追加到已发布笔记。

注意：
- 剧照版权归原出品方/发行方，公开平台使用建议注明出处。
- 需要 TMDB 网页可达（无验证码的常规抓取即可，无需 API key）。
- 给已发布笔记配图需要浏览器调试端口 9222 + cdp-proxy(3456) 且已登录小红书创作者中心。
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

# 已知电影 slug -> TMDB id（赫尔佐格回顾展四部曲，2026-08 北京中国电影资料馆）
KNOWN_TMDB = {
    "kaspar_hauser": 11710,   # Jeder für sich und Gott gegen alle (1974)
    "stroszek": 11698,        # Stroszek (1977)
    "woyzeck": 10319,         # Woyzeck (1979) — 注意不是 1368217
    "nosferatu": 6404,        # Nosferatu: Phantom der Nacht (1979)
}


def http_get(url: str, timeout: int = 40) -> str:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def resolve_tmdb_id(slug: str | None, tmdb_id: int | None) -> int:
    if tmdb_id:
        return tmdb_id
    if slug and slug in KNOWN_TMDB:
        return KNOWN_TMDB[slug]
    raise RuntimeError("需要 --tmdb-id，或 --slug 命中内置映射（kaspar_hauser/stroszek/woyzeck/nosferatu）")


def get_backdrops_url(tmdb_id: int) -> tuple[str, str]:
    """返回 (backdrops_url, movie_title)。"""
    page = http_get(f"https://www.themoviedb.org/movie/{tmdb_id}")
    m = re.search(r'href="(/movie/[^"]+/images/backdrops)"', page)
    if not m:
        raise RuntimeError(f"电影页未找到 images/backdrops 链接 (id={tmdb_id})")
    title = re.search(r"<title>([^<]+)</title>", page)
    return "https://www.themoviedb.org" + m.group(1), (title.group(1) if title else "")


def parse_backdrops(html: str) -> list[dict]:
    items = re.findall(r'<li id="[0-9a-f]+" class="card compact ok".*?</li>', html, re.S)
    rows = []
    for it in items:
        murl = re.search(r'https://image\.tmdb\.org/t/p/original(/[^"\'\\ ]+)', it)
        msize = re.search(r'target="_blank">(\d+)x(\d+)</a>', it)
        if not murl:
            continue
        w = h = 0
        if msize:
            w, h = int(msize.group(1)), int(msize.group(2))
        rows.append({"path": murl.group(1), "w": w, "h": h})
    return rows


def download(url: str, dest: Path) -> None:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=90) as resp:
        data = resp.read()
    dest.write_bytes(data)


def main() -> int:
    ap = argparse.ArgumentParser(description="TMDB 高清剧照下载 + 可选小红书配图")
    ap.add_argument("--tmdb-id", type=int, help="TMDB 电影 id")
    ap.add_argument("--slug", help="电影 slug（内置映射：kaspar_hauser/stroszek/woyzeck/nosferatu）")
    ap.add_argument("--count", type=int, default=6, help="下载张数（按评分最高取前 N）")
    ap.add_argument("--min-width", type=int, default=1280, help="最小宽度过滤，默认 1280")
    ap.add_argument("--out-dir", required=True, help="剧照保存目录")
    ap.add_argument("--note-id", help="已发布小红书笔记 id；给出则自动追加配图（仅配图模式，不改文案）")
    ap.add_argument("--no-publish", action="store_true", help="配图只填充不点发布（人工核对）")
    ap.add_argument("--dry-run", action="store_true", help="只解析和下载列表，不上传")
    ap.add_argument("--proxy", default="http://127.0.0.1:3456", help="CDP 代理地址（配图时用）")
    ap.add_argument("--publish-timeout", type=int, default=60)
    args = ap.parse_args()

    tmdb_id = resolve_tmdb_id(args.slug, args.tmdb_id)
    backdrops_url, title = get_backdrops_url(tmdb_id)
    html = http_get(backdrops_url + "?image_sort=rating.desc")
    rows = [r for r in parse_backdrops(html) if r["w"] >= args.min_width]
    if not rows:
        raise RuntimeError(f"未找到宽度 >= {args.min_width} 的 backdrops（id={tmdb_id}）")
    picks = rows[: args.count]

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    slug = args.slug or f"tmdb_{tmdb_id}"
    files = []
    for i, row in enumerate(picks, 1):
        dest = out_dir / f"{slug}_still_{i}.jpg"
        if not args.dry_run:
            download("https://image.tmdb.org/t/p/original" + row["path"], dest)
        files.append({"file": str(dest), "width": row["w"], "height": row["h"], "tmdb_path": row["path"]})

    result = {
        "ok": True,
        "tmdb_id": tmdb_id,
        "title": title,
        "backdrops_url": backdrops_url,
        "picked": files,
        "note_id": args.note_id,
        "dry_run": args.dry_run,
        "copyright": "剧照版权归原出品方/发行方所有",
    }

    if args.note_id and files and not args.dry_run:
        py = sys.executable
        script = Path(__file__).resolve().parent / "xhs_publish.py"
        cmd = [py, str(script), "update", "--note-id", args.note_id, "--proxy", args.proxy,
               "--publish-timeout", str(args.publish_timeout)]
        if args.no_publish:
            cmd.append("--no-publish")
        for f in files:
            cmd += ["--image", f["file"]]
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
        out = (proc.stdout or "").strip() or (proc.stderr or "").strip()
        try:
            parsed = json.loads(out)
        except Exception:
            parsed = {"raw": out[-2000:]}
        result["publish"] = parsed

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
