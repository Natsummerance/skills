#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""xhs_publish.py — 小红书全自动发布脚本（CDP 代理驱动已登录 Edge/Chrome）

依赖：
- 浏览器以 --remote-debugging-port 启动（Edge 143+：--remote-allow-origins=*）
- web-access skill 的 cdp-proxy.mjs 正在 3456 端口运行
- 浏览器已登录 creator.xiaohongshu.com

命令：
  publish     全自动发布（默认）
  update      编辑已发布笔记（/publish/update?id=...）并重新发布
  draft       填充但不点发布（人工核对）
  status      查询笔记审核状态（--note-title 或 --note-id）
  login       仅检查登录态
  tabs        列出代理可见的页面 tab

用法示例：
  python xhs_publish.py publish ^
      --title "标题" --body "正文..." ^
      --cover C:/path/cover.png --image C:/path/img2.png ^
      --topic "赫尔佐格" --topic "中国电影资料馆"

注意：正文/标题中出现 公众号/微信/闲鱼/转卖/出票 等词会触发审核失败，
脚本默认拦截，用 --force 才放行。
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

PUBLISH_URL = "https://creator.xiaohongshu.com/publish/publish?source=official"
NOTE_MANAGER_URL = "https://creator.xiaohongshu.com/new/note-manager?source=official"
DEFAULT_PROXY = "http://127.0.0.1:3456"
SCRIPT_DIR = Path(__file__).resolve().parent

BANNED_WORDS = [
    "公众号", "微信", "加微信", "vx", "weixin", "闲鱼", "咸鱼",
    "转卖", "出票", "转让", "售票", "二维码", "淘口令", "淘宝",
]

# ---------------------------------------------------------------------------
# HTTP 工具
# ---------------------------------------------------------------------------

PROXY = DEFAULT_PROXY


def http(method: str, path: str, body=None, timeout: int = 60):
    url = PROXY + path
    data = None
    headers = {}
    if body is not None:
        if isinstance(body, str):
            data = body.encode("utf-8")
            headers["Content-Type"] = "text/plain; charset=utf-8"
        else:
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json; charset=utf-8"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = resp.read().decode("utf-8", errors="replace")
            try:
                return json.loads(payload)
            except Exception:
                return payload
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} {path}: {detail[:300]}")
    except Exception as exc:
        raise RuntimeError(f"请求失败 {path}: {exc}")


def eval_js(target: str, js: str, timeout: int = 30):
    r = http("POST", f"/eval?target={target}", js, timeout=timeout)
    if isinstance(r, dict) and r.get("error"):
        raise RuntimeError(f"页面 JS 错误: {r['error']}")
    return r.get("value") if isinstance(r, dict) else r


def set_files(target: str, selector: str, files: list):
    return http("POST", f"/setFiles?target={target}",
                {"selector": selector, "files": files}, timeout=120)


def click(target: str, selector: str):
    return http("POST", f"/click?target={target}", selector, timeout=30)


def click_at(target: str, selector: str):
    return http("POST", f"/clickAt?target={target}", selector, timeout=30)


def navigate(target: str, url: str):
    return http("POST", f"/navigate?target={target}", url, timeout=90)


def info(target: str):
    return eval_js(target, "(() => ({ url: location.href, title: document.title, ready: document.readyState }))()")


def new_tab(url: str):
    r = http("POST", "/new", url, timeout=90)
    return r.get("targetId")


def list_targets():
    r = http("GET", "/targets", timeout=15)
    if isinstance(r, list):
        return r
    if isinstance(r, dict) and isinstance(r.get("targets"), list):
        return r["targets"]
    return []


# ---------------------------------------------------------------------------
# 页面 JS 片段
# ---------------------------------------------------------------------------

JS_FIND_PUBLISH_TAB = """
(() => {
  const t = document.querySelector('input[placeholder="填写标题会有更多赞哦"]');
  return { onPublish: location.href.includes('/publish/publish'), hasTitleInput: !!t };
})()
"""

JS_ENSURE_IMAGE_MODE = """
(() => {
  const tabs = Array.from(document.querySelectorAll('.creator-tab'));
  const visible = tabs.filter(t => !((t.getAttribute('style')||'').includes('left: -9999px')));
  const active = visible.find(t => (t.className||'').includes('active'));
  const activeText = active ? (active.innerText||'').trim() : '';
  if (activeText.includes('上传图文')) return { ok: true, mode: 'image', activeText };
  const imageTab = visible.find(t => (t.innerText||'').includes('上传图文'));
  if (imageTab) { imageTab.click(); return { ok: true, switched: true, mode: 'image' }; }
  return { ok: false, activeText };
})()
"""

JS_UPLOAD_READY = """
(() => {
  const inputs = Array.from(document.querySelectorAll('input[type=file]'));
  const imgInput = inputs.find(i => (i.accept||'').includes('.jpg'));
  return { hasImageInput: !!imgInput, hasTitleInput: !!document.querySelector('input[placeholder="填写标题会有更多赞哦"]') };
})()
"""

JS_IMG_COUNT = """
(() => {
  const el = Array.from(document.querySelectorAll('div.status')).find(e => /^\\d+\\/18$/.test((e.innerText||'').trim()));
  if (!el) return -1;
  const m = (el.innerText||'').trim().match(/^(\\d+)\\/18$/);
  return m ? parseInt(m[1], 10) : -1;
})()
"""

JS_SET_TITLE = """
(() => {
  const input = document.querySelector('input[placeholder="填写标题会有更多赞哦"]');
  if (!input) return { ok: false, error: '标题输入框未找到' };
  const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
  setter.call(input, __TITLE__);
  input.dispatchEvent(new Event('input', { bubbles: true }));
  input.dispatchEvent(new Event('change', { bubbles: true }));
  return { ok: true, value: input.value };
})()
"""

JS_SET_BODY = """
(() => {
  const editor = document.querySelector('.tiptap.ProseMirror');
  if (!editor) return { ok: false, error: '正文编辑器未找到' };
  editor.focus();
  const sel = window.getSelection();
  sel.selectAllChildren(editor);
  sel.collapseToEnd();
  document.execCommand('insertText', false, __BODY__);
  return { ok: true, preview: (editor.innerText||'').slice(0, 60) };
})()
"""

JS_ADD_TOPIC = """
(async () => {
  const editor = document.querySelector('.tiptap.ProseMirror');
  if (!editor) return { ok: false, error: '正文编辑器未找到', topic: __TOPIC__ };
  editor.focus();
  const sel = window.getSelection();
  sel.selectAllChildren(editor);
  sel.collapseToEnd();
  document.execCommand('insertText', false, '\\n#' + __TOPIC__);
  for (let i = 0; i < 12; i++) {
    await new Promise(r => setTimeout(r, 300));
    const container = document.querySelector('#creator-editor-topic-container');
    if (!container) continue;
    const items = Array.from(container.querySelectorAll('.item'));
    if (!items.length) continue;
    const prefix = '#' + __TOPIC__ + '\\n';
    const exact = items.find(it => (it.innerText||'').trim().startsWith(prefix)) || items[0];
    exact.click();
    await new Promise(r => setTimeout(r, 500));
    const inserted = Array.from(editor.querySelectorAll('a.tiptap-topic')).some(a => (a.innerText||'').includes('#' + __TOPIC__));
    return { ok: true, topic: __TOPIC__, inserted };
  }
  return { ok: false, error: '话题弹层未出现', topic: __TOPIC__ };
})()
"""

JS_TOPIC_FALLBACK = """
(async () => {
  const btn = document.querySelector('.contentBtn.topic-btn');
  const editor = document.querySelector('.tiptap.ProseMirror');
  if (!btn || !editor) return { ok: false, error: '话题按钮或编辑器未找到' };
  btn.click();
  await new Promise(r => setTimeout(r, 400));
  editor.focus();
  const sel = window.getSelection();
  sel.selectAllChildren(editor);
  sel.collapseToEnd();
  document.execCommand('insertText', false, __TOPIC__);
  document.execCommand('insertText', false, ' ');
  return { ok: true, topic: __TOPIC__, method: 'topic-btn' };
})()
"""

JS_PUBLISH = """
(() => {
  const btn = document.querySelector('xhs-publish-btn');
  if (!btn) return { ok: false, error: '发布按钮(xhs-publish-btn)未找到' };
  btn.dispatchEvent(new CustomEvent('publish', { bubbles: true, composed: true }));
  return { ok: true };
})()
"""

JS_PUBLISH_STATE = """
(() => {
  const url = location.href;
  if (url.includes('published=true')) return 'published';
  const onPublish = url.includes('/publish/publish') || url.includes('/publish/update');
  if (!onPublish) {
    if (url.includes('/login') || url.includes('/passport')) {
      return { state: 'error', text: '页面跳转到登录页，需重新登录' };
    }
    return 'published';
  }
  const texts = Array.from(document.querySelectorAll('[class*="message"],[class*="toast"],[class*="notice"],[role="alert"]'))
    .map(n => (n.innerText || '').trim()).filter(Boolean);
  const joined = texts.join(' ');
  if (/发布成功|发布完成|已发布|保存成功|更新成功/.test(joined)) return 'published';
  if (/标题最多输入|最多输入20字|不能为空|请填写|发布失败|操作失败|网络错误/.test(joined)) {
    return { state: 'error', text: joined.slice(0, 200) };
  }
  const btn = document.querySelector('xhs-publish-btn');
  const btnText = (btn && btn.innerText || '').trim();
  if (btnText && /发布中/.test(btnText)) return 'published';
  return 'pending';
})()
"""

JS_CLEAR_TOASTS = """
(() => {
  const nodes = Array.from(document.querySelectorAll('[class*="message"],[class*="toast"],[class*="notice"],[role="alert"]'));
  nodes.forEach(n => n.remove());
  return nodes.length;
})()
"""

JS_LAST_TOAST = """
(() => {
  const texts = Array.from(document.querySelectorAll('[class*="message"],[class*="toast"],[class*="notice"],[role="alert"]'))
    .map(n => (n.innerText || '').trim()).filter(Boolean);
  return { url: location.href, toasts: texts.slice(-3) };
})()
"""

JS_UPDATE_READY = """
(() => ({
  ok: !!document.querySelector('input[placeholder="填写标题会有更多赞哦"]') && !!document.querySelector('.tiptap.ProseMirror'),
  hasPublishBtn: !!document.querySelector('xhs-publish-btn'),
}))()
"""

JS_CLEAR_BODY = """
(() => {
  const editor = document.querySelector('.tiptap.ProseMirror');
  if (!editor) return { ok: false, error: '正文编辑器未找到' };
  editor.focus();
  const range = document.createRange();
  range.selectNodeContents(editor);
  const sel = window.getSelection();
  sel.removeAllRanges();
  sel.addRange(range);
  document.execCommand('delete');
  return { ok: true, len: (editor.innerText || '').length };
})()
"""

JS_NOTE_MANAGER_READY = """
(() => !!document.querySelector('.note-card, .tab-item'))()
"""

JS_CLICK_FILTER_TAB = """
(() => {
  const tabs = Array.from(document.querySelectorAll('.tab-item'));
  const target = tabs.find(t => (t.innerText||'').trim() === __TAB__);
  if (!target) return { ok: false };
  target.click();
  return { ok: true };
})()
"""

JS_FIND_NOTE = """
(() => {
  const cards = Array.from(document.querySelectorAll('.note-card'));
  let card = null;
  if (__NOTE_ID__) {
    card = cards.find(c => ((c.getAttribute('data-impression')||'').includes(__NOTE_ID__)));
  }
  if (!card && __TITLE__) {
    card = cards.find(c => (((c.querySelector('.note-card__title')||{}).innerText||'').trim() === __TITLE__));
  }
  if (!card) return { found: false };
  const idMatch = ((card.getAttribute('data-impression')||'').match(/noteId\\":\\"([0-9a-f]+)/));
  return { found: true, noteId: idMatch ? idMatch[1] : null };
})()
"""

JS_READ_AUDIT_MODAL = """
(() => {
  const modal = document.querySelector('.audit-modal');
  if (!modal) return { found: false };
  return { found: true, text: (modal.innerText||'').slice(0, 600) };
})()
"""

JS_CLICK_MODIFY_SUGGESTION = """
(() => {
  const btns = Array.from(document.querySelectorAll('button, .btn, [class*="btn"], span, div'));
  const target = btns.find(b => (b.innerText||'').trim().includes('查看修改建议'));
  if (!target) return { ok: false };
  target.click();
  return { ok: true };
})()
"""


def _js(template: str, **kwargs) -> str:
    out = template
    for key, val in kwargs.items():
        if key in ("__TITLE__", "__BODY__", "__TOPIC__", "__TAB__"):
            out = out.replace(key, json.dumps(val, ensure_ascii=False))
        else:
            out = out.replace(key, json.dumps(val))
    return out


# ---------------------------------------------------------------------------
# 流程步骤
# ---------------------------------------------------------------------------

def strip_trailing_topic_line(body: str) -> str:
    """去掉正文末尾纯话题行（如 '#赫尔佐格 #电影 ...'），避免与 --topic 添加的话题重复。"""
    lines = body.splitlines()
    while lines:
        line = lines[-1].strip()
        if line and re.fullmatch(r"(#\S+\s*)+", line):
            lines.pop()
        else:
            break
    return "\n".join(lines).strip()


def check_banned_words(title: str, body: str) -> list:
    hits = []
    for word in BANNED_WORDS:
        if word in (title or "") or word in (body or ""):
            hits.append(word)
    return hits


def open_publish_tab() -> str:
    """找到或新建一个发布页 tab。优先复用已停留在发布页的 tab。"""
    for t in list_targets():
        url = (t.get("url") or "")
        if "/publish/publish" in url:
            return t["targetId"]
    target = new_tab(PUBLISH_URL)
    time.sleep(2)
    return target


def open_update_tab(note_id: str) -> str:
    """找到或新建一个已发布笔记的编辑页 tab（/publish/update?id=...）。"""
    for t in list_targets():
        url = (t.get("url") or "")
        if f"/publish/update?id={note_id}" in url:
            return t["targetId"]
    target = new_tab(f"https://creator.xiaohongshu.com/publish/update?id={note_id}")
    time.sleep(3)
    return target


def ensure_login(target: str) -> None:
    for _ in range(6):
        p = info(target)
        url = p.get("url", "")
        if "login" in url or "passport" in url:
            raise RuntimeError("未登录：页面跳转到登录页。请在浏览器中手动完成登录后重试。")
        if "creator.xiaohongshu.com" in url and "/publish/" in url:
            return
        time.sleep(2)
    raise RuntimeError(f"无法确认登录态，当前页面: {info(target)}")


def ensure_image_mode(target: str) -> None:
    """确保发布页处于图文模式。

    - 已有图片上传框（.jpg accept 的 input）→ 已在图文模式，直接返回；
    - 否则在 .creator-tab 中点击「上传图文」；
    - 注意：进入图文编辑后 .creator-tab 会从 DOM 移除，不能仅靠它判断。
    """
    for _ in range(25):
        u = eval_js(target, JS_UPLOAD_READY, timeout=20)
        if u.get("hasImageInput"):
            return
        r = eval_js(target, JS_ENSURE_IMAGE_MODE, timeout=20)
        if r.get("ok"):
            break
        time.sleep(1)
    # 切换后等待图片上传框出现
    for _ in range(15):
        u = eval_js(target, JS_UPLOAD_READY, timeout=20)
        if u.get("hasImageInput"):
            return
        time.sleep(1)
    raise RuntimeError(f"无法切换到图文模式（未出现图片上传框）: {r}")
    # 等待图片上传框出现
    for _ in range(15):
        u = eval_js(target, JS_UPLOAD_READY)
        if u.get("hasImageInput"):
            return
        time.sleep(1)
    raise RuntimeError("切换到图文模式后未出现图片上传框")


def upload_images(target: str, files: list) -> int:
    """files[0] 为封面；逐张上传并等待计数增加。返回已上传张数。"""
    expected_total = len(files)
    uploaded = 0
    # 第一张（封面）：原始 .upload-input
    r = set_files(target, "input[type=file].upload-input", [str(files[0])])
    uploaded += 1
    # 等待编辑器出现（第一张图后渲染编辑器）
    for _ in range(20):
        u = eval_js(target, JS_UPLOAD_READY)
        if u.get("hasTitleInput"):
            break
        time.sleep(1)
    time.sleep(2)
    # 其余配图：隐藏的图片 input
    for path in files[1:]:
        set_files(target, "input[type=file][accept*='.jpg']", [str(path)])
        uploaded += 1
        # 等计数到达 uploaded
        for _ in range(20):
            n = eval_js(target, JS_IMG_COUNT)
            if n >= uploaded:
                break
            time.sleep(1)
        time.sleep(1)
    return uploaded


def _current_image_count(target: str) -> int:
    n = eval_js(target, JS_IMG_COUNT)
    return n if isinstance(n, int) and n >= 0 else 0


def add_images_update(target: str, files: list) -> int:
    """编辑页（/publish/update）追加图片：逐张通过隐藏 jpg input 上传并等待计数增加。"""
    base = _current_image_count(target)
    uploaded = 0
    for path in files:
        set_files(target, "input[type=file][accept*='.jpg']", [str(path)])
        uploaded += 1
        for _ in range(20):
            n = _current_image_count(target)
            if n >= base + uploaded:
                break
            time.sleep(1)
        time.sleep(1)
    return uploaded


def fill_title(target: str, title: str) -> None:
    r = eval_js(target, _js(JS_SET_TITLE, __TITLE__=title))
    if not r.get("ok"):
        raise RuntimeError(f"填写标题失败: {r}")
    time.sleep(0.5)


def fill_body(target: str, body: str) -> None:
    r = eval_js(target, _js(JS_SET_BODY, __BODY__=body))
    if not r.get("ok"):
        raise RuntimeError(f"填写正文失败: {r}")
    time.sleep(0.5)


def add_topics(target: str, topics: list) -> list:
    results = []
    for topic in topics:
        topic = topic.lstrip("#").strip()
        if not topic:
            continue
        try:
            r = eval_js(target, _js(JS_ADD_TOPIC, __TOPIC__=topic), timeout=30)
        except RuntimeError:
            r = {"ok": False}
        if not r.get("ok"):
            # 兜底：直接点话题按钮插入
            r2 = eval_js(target, _js(JS_TOPIC_FALLBACK, __TOPIC__=topic), timeout=20)
            results.append({"topic": topic, "ok": bool(r2.get("ok")), "method": "fallback"})
        else:
            results.append({"topic": topic, "ok": True, "method": "popup"})
        time.sleep(0.8)
    return results


def do_publish(target: str, timeout: int = 60) -> None:
    try:
        eval_js(target, JS_CLEAR_TOASTS, timeout=10)
    except RuntimeError:
        pass
    r = eval_js(target, JS_PUBLISH)
    if not r.get("ok"):
        raise RuntimeError(f"触发发布失败: {r}")
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            state = eval_js(target, JS_PUBLISH_STATE, timeout=15)
        except RuntimeError:
            state = "pending"
        if isinstance(state, dict) and state.get("state") == "error":
            raise RuntimeError(f"发布被拦截: {state.get('text')}")
        if state == "published":
            return
        time.sleep(2)
    raise RuntimeError("发布后未检测到跳转（可能弹出了确认框或发布失败）")


def screenshot(target: str, path: str) -> None:
    try:
        http("GET", f"/screenshot?target={target}&file={path}", timeout=30)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# 状态查询
# ---------------------------------------------------------------------------

def get_note_status(target: str, note_id: str | None = None, note_title: str | None = None) -> dict:
    """在笔记管理页用筛选 tab 判断笔记状态。"""
    for tab_name in ("审核中", "已发布", "未通过"):
        eval_js(target, _js(JS_CLICK_FILTER_TAB, __TAB__=tab_name))
        time.sleep(2.5)
        finder = _js(JS_FIND_NOTE, __NOTE_ID__=note_id or "", __TITLE__=note_title or "")
        r = eval_js(target, finder, timeout=20)
        if r.get("found"):
            result = {"status": tab_name, "noteId": r.get("noteId") or note_id}
            if tab_name == "未通过":
                eval_js(target, JS_CLICK_MODIFY_SUGGESTION)
                time.sleep(1.5)
                modal = eval_js(target, JS_READ_AUDIT_MODAL, timeout=20)
                result["auditReason"] = modal.get("text") if modal.get("found") else None
            return result
    # 回到全部
    eval_js(target, _js(JS_CLICK_FILTER_TAB, __TAB__="全部"))
    return {"status": "未知", "noteId": note_id}


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def cmd_publish(args):
    global PROXY
    PROXY = args.proxy

    if getattr(args, "bootstrap_edge", False):
        if args.dry_run:
            raise RuntimeError("--dry-run 不需要启动浏览器；请移除 --bootstrap-edge")
        command = [sys.executable, str(SCRIPT_DIR / "bootstrap_edge_cdp.py")]
        if args.restart_edge:
            command.append("--restart-edge")
        prepared = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
        if prepared.returncode:
            raise RuntimeError("Edge/CDP 准备失败: " + (prepared.stdout or prepared.stderr).strip())

    # 输入校验
    if args.title_file:
        args.title = Path(args.title_file).read_text(encoding="utf-8").strip()
    if args.body_file:
        args.body = Path(args.body_file).read_text(encoding="utf-8").strip()
    if args.topics:
        args.body = strip_trailing_topic_line(args.body)
    if not args.title or not args.body:
        raise RuntimeError("需要 --title/--title-file 与 --body/--body-file")
    banned = check_banned_words(args.title, args.body)
    if banned and not args.force:
        raise RuntimeError(
            "正文/标题包含可能触发审核的词: " + ", ".join(banned) +
            "。这些词（公众号/微信/闲鱼/转卖/出票等）会触发「推广第三方平台」审核失败。" +
            "请删除后重试；确需保留请加 --force。"
        )
    files = []
    if args.cover:
        files.append(args.cover)
    if args.images:
        files.extend(args.images)
    if not files:
        raise RuntimeError("至少需要一张封面图（--cover）")
    for f in files:
        p = Path(f)
        if not p.exists():
            raise RuntimeError(f"图片不存在: {f}")
        if p.stat().st_size > 32 * 1024 * 1024:
            raise RuntimeError(f"图片超过 32MB 上限: {f}")

    if args.dry_run:
        print(json.dumps({
            "dryRun": True,
            "title": args.title,
            "bodyChars": len(args.body),
            "images": files,
            "topics": args.topics,
            "bannedWords": banned,
        }, ensure_ascii=False, indent=2))
        return

    target = open_publish_tab()
    ensure_login(target)
    ensure_image_mode(target)
    uploaded = upload_images(target, files)
    fill_title(target, args.title)
    fill_body(target, args.body)
    topics = add_topics(target, args.topics)

    # 校验预览
    preview = eval_js(target, """
    (() => ({
      title: (document.querySelector('input[placeholder="填写标题会有更多赞哦"]')||{}).value || '',
      body: (document.querySelector('.tiptap.ProseMirror')||{}).innerText || '',
      topics: Array.from(document.querySelectorAll('a.tiptap-topic')).map(a => (a.innerText||'').trim()),
    }))()
    """)

    if args.no_publish:
        print(json.dumps({
            "published": False,
            "mode": "draft",
            "targetId": target,
            "imagesUploaded": uploaded,
            "preview": preview,
            "topicResults": topics,
            "next": "请在浏览器预览后手动点击发布，或运行 status 命令跟踪状态",
        }, ensure_ascii=False, indent=2))
        return

    do_publish(target, timeout=args.publish_timeout)
    print(json.dumps({
        "published": True,
        "targetId": target,
        "imagesUploaded": uploaded,
        "title": args.title,
        "topicResults": topics,
        "next": "审核状态可用 status --note-title '<标题>' 查询",
    }, ensure_ascii=False, indent=2))


def cmd_update(args):
    """编辑已发布笔记：打开 /publish/update?id=<noteId>，改标题/正文/话题后重新发布；也可只追加配图（--image，不改文案）。"""
    global PROXY
    PROXY = args.proxy
    if not args.note_id:
        raise RuntimeError("需要 --note-id")
    if args.title_file:
        args.title = Path(args.title_file).read_text(encoding="utf-8").strip()
    if args.body_file:
        args.body = Path(args.body_file).read_text(encoding="utf-8").strip()
    if args.topics:
        args.body = strip_trailing_topic_line(args.body)
    images_only = bool(args.images) and not (args.title and args.body)
    if not args.title and not args.body and not args.images:
        raise RuntimeError("需要 --title/--title-file 与 --body/--body-file，或提供 --image 只追加配图（不改文案）")
    banned = check_banned_words(args.title or "", args.body or "")
    if banned and not args.force:
        raise RuntimeError(
            "正文/标题包含可能触发审核的词: " + ", ".join(banned) +
            "。这些词会触发「推广第三方平台」审核失败。请删除后重试；确需保留请加 --force。"
        )
    if args.dry_run:
        print(json.dumps({
            "dryRun": True,
            "command": "update",
            "noteId": args.note_id,
            "title": args.title,
            "bodyChars": len(args.body or ""),
            "images": args.images,
            "imagesOnly": images_only,
            "topics": args.topics,
            "bannedWords": banned,
        }, ensure_ascii=False, indent=2))
        return

    target = open_update_tab(args.note_id)
    ensure_login(target)
    ready = False
    for _ in range(25):
        u = eval_js(target, JS_UPDATE_READY, timeout=20)
        if u.get("ok"):
            ready = True
            break
        time.sleep(1)
    if not ready:
        raise RuntimeError(f"编辑页未就绪（找不到标题输入框/正文编辑器）: {u}")
    time.sleep(1)

    added_images = add_images_update(target, args.images) if args.images else 0
    time.sleep(1)

    topics = []
    if args.title and args.body:
        fill_title(target, args.title)
        r = eval_js(target, JS_CLEAR_BODY)
        if not r.get("ok"):
            raise RuntimeError(f"清空正文失败: {r}")
        fill_body(target, args.body)
        topics = add_topics(target, args.topics)

    preview = eval_js(target, """
    (() => ({
      title: (document.querySelector('input[placeholder="填写标题会有更多赞哦"]')||{}).value || '',
      body: (document.querySelector('.tiptap.ProseMirror')||{}).innerText || '',
      topics: Array.from(document.querySelectorAll('a.tiptap-topic')).map(a => (a.innerText||'').trim()),
    }))()
    """)

    if args.no_publish:
        print(json.dumps({
            "published": False,
            "mode": "draft-update",
            "noteId": args.note_id,
            "targetId": target,
            "preview": preview,
            "topicResults": topics,
            "next": "请在浏览器预览后手动点击发布",
        }, ensure_ascii=False, indent=2))
        return

    do_publish(target, timeout=args.publish_timeout)
    dbg = eval_js(target, JS_LAST_TOAST, timeout=15)
    print(json.dumps({
        "published": True,
        "mode": "update",
        "noteId": args.note_id,
        "targetId": target,
        "addedImages": added_images,
        "title": args.title,
        "topicResults": topics,
        "pageAfterPublish": dbg,
        "next": "审核状态可用 status --note-id '<noteId>' 查询",
    }, ensure_ascii=False, indent=2))


def cmd_status(args):
    global PROXY
    PROXY = args.proxy
    if not args.note_id and not args.note_title:
        raise RuntimeError("需要 --note-id 或 --note-title")
    target = None
    for t in list_targets():
        if "note-manager" in (t.get("url") or ""):
            target = t["targetId"]
            break
    if not target:
        target = new_tab(NOTE_MANAGER_URL)
    time.sleep(3)
    result = get_note_status(target, note_id=args.note_id, note_title=args.note_title)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_login(args):
    global PROXY
    PROXY = args.proxy
    target = open_publish_tab()
    try:
        ensure_login(target)
        print(json.dumps({"loggedIn": True, "targetId": target}, ensure_ascii=False, indent=2))
    except RuntimeError as exc:
        print(json.dumps({"loggedIn": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        sys.exit(1)


def cmd_tabs(args):
    global PROXY
    PROXY = args.proxy
    print(json.dumps(list_targets(), ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description="小红书全自动发布（CDP 代理）")
    sub = parser.add_subparsers(dest="command")

    p = sub.add_parser("publish", help="全自动发布")
    p.add_argument("--proxy", default=DEFAULT_PROXY)
    p.add_argument("--title")
    p.add_argument("--title-file", help="从文件读取标题（优先于 --title）")
    p.add_argument("--body")
    p.add_argument("--body-file", help="从文件读取正文（优先于 --body）")
    p.add_argument("--cover", help="封面图（第一张）")
    p.add_argument("--image", dest="images", action="append", default=[], help="配图（可多次）")
    p.add_argument("--topic", dest="topics", action="append", default=[], help="话题标签（可多次，无需 #）")
    p.add_argument("--no-publish", action="store_true", help="只填充不发布（草稿模式）")
    p.add_argument("--dry-run", action="store_true", help="只校验输入，不操作浏览器")
    p.add_argument("--force", action="store_true", help="放行含敏感词的文案（不建议）")
    p.add_argument("--publish-timeout", type=int, default=60)
    p.add_argument("--bootstrap-edge", action="store_true", help="先确认默认 Edge 的 CDP 调试端口")
    p.add_argument("--restart-edge", action="store_true", help="与 --bootstrap-edge 一起使用：关闭并重启默认 Edge")

    p = sub.add_parser("draft", help="填充但停在发布前")
    p.add_argument("--proxy", default=DEFAULT_PROXY)
    p.add_argument("--title")
    p.add_argument("--title-file")
    p.add_argument("--body")
    p.add_argument("--body-file")
    p.add_argument("--cover")
    p.add_argument("--image", dest="images", action="append", default=[])
    p.add_argument("--topic", dest="topics", action="append", default=[])
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--force", action="store_true")

    p = sub.add_parser("update", help="编辑已发布笔记并重新发布")
    p.add_argument("--proxy", default=DEFAULT_PROXY)
    p.add_argument("--note-id", required=True)
    p.add_argument("--title")
    p.add_argument("--title-file")
    p.add_argument("--body")
    p.add_argument("--body-file")
    p.add_argument("--image", dest="images", action="append", default=[], help="追加配图（可多次）")
    p.add_argument("--topic", dest="topics", action="append", default=[])
    p.add_argument("--no-publish", action="store_true", help="只填充不发布（草稿模式）")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--force", action="store_true")
    p.add_argument("--publish-timeout", type=int, default=60)

    p = sub.add_parser("status", help="查询笔记审核状态")
    p.add_argument("--proxy", default=DEFAULT_PROXY)
    p.add_argument("--note-id")
    p.add_argument("--note-title")

    p = sub.add_parser("login", help="检查登录态")
    p.add_argument("--proxy", default=DEFAULT_PROXY)

    p = sub.add_parser("tabs", help="列出页面 tab")
    p.add_argument("--proxy", default=DEFAULT_PROXY)

    p = sub.add_parser("bootstrap", help="确认默认 Edge 的 CDP 调试端口")
    p.add_argument("--restart-edge", action="store_true", help="关闭全部 Edge 后重启默认 profile")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(2)

    try:
        if args.command == "publish":
            cmd_publish(args)
        elif args.command == "draft":
            args.no_publish = True
            cmd_publish(args)
        elif args.command == "update":
            cmd_update(args)
        elif args.command == "status":
            cmd_status(args)
        elif args.command == "login":
            cmd_login(args)
        elif args.command == "tabs":
            cmd_tabs(args)
        elif args.command == "bootstrap":
            command = [sys.executable, str(SCRIPT_DIR / "bootstrap_edge_cdp.py")]
            if args.restart_edge:
                command.append("--restart-edge")
            raise SystemExit(subprocess.call(command))
    except RuntimeError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
