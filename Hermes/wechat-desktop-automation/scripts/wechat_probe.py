#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
wechat_probe.py — 微信 4.0 桌面自动化诊断探针（2026-08-05 实测可用）
用法:
    python wechat_probe.py --pid 30764 --wid 20253098           # 只截图对比三种源
    python wechat_probe.py --pid 30764 --wid 20253098 --click-logical 518,302   # PostMessage 点击(逻辑frame坐标)
    python wechat_probe.py --pid 30764 --wid 20253098 --keys ctrl+f               # 键盘 Ctrl+F

核心结论（本会话实测）:
  1. 真实鼠标(SetCursorPos+mouse_event)对微信 4.0 无效 (diff=0)，即使 GetWindowFromPoint 显示微信在顶层
  2. PostMessageW WM_LBUTTONDOWN/UP 有效（客户区物理坐标）
  3. keybd_event 键盘有效（Ctrl+F 搜索/粘贴/Enter 都有大 diff）
  4. 三种截图源可能互相矛盾：cua-driver 官方 / BitBlt 屏幕 DC / PrintWindow —— 判活靠交互 diff 不靠截图
"""
import subprocess, json, base64, io, sys, time, ctypes
from ctypes import wintypes
from PIL import Image

CUA = r"C:\Users\Natsumer\AppData\Local\Programs\Cua\cua-driver\bin\cua-driver.exe"
user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32


def cua_call(cmd, args):
    """cua-driver CLI 容错解析：stdout 可能混入额外内容，截取首个{到末个}。失败可能只返回 {"pid": N}。"""
    r = subprocess.run([CUA, "call", cmd, json.dumps(args)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=90)
    i, j = r.stdout.find("{"), r.stdout.rfind("}")
    if i < 0 or j < i:
        return {"raw": r.stdout[:200]}
    try:
        return json.loads(r.stdout[i:j + 1])
    except Exception:
        return {}


def grab_cua(pid, wid):
    """cua-driver 官方截图（逻辑像素，base64 解码）。"""
    d = cua_call("get_window_state", {"pid": pid, "window_id": wid, "max_elements": 50})
    b64 = d.get("screenshot_png_b64")
    if not b64:
        return None
    return Image.open(io.BytesIO(base64.b64decode(b64))).convert("RGB")


def grab_bitblt(hwnd):
    """BitBlt 从屏幕 DC 截取窗口区域（真实屏幕合成帧，物理像素）。"""
    r = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(r))
    W, H = r.right - r.left, r.bottom - r.top
    hdc = user32.GetDC(0)
    mdc = gdi32.CreateCompatibleDC(hdc)
    bmp = gdi32.CreateCompatibleBitmap(hdc, W, H)
    gdi32.SelectObject(mdc, bmp)
    gdi32.BitBlt(mdc, 0, 0, W, H, hdc, r.left, r.top, 0x00CC0020)  # SRCCOPY

    class BIH(ctypes.Structure):
        _fields_ = [("biSize", ctypes.c_uint32), ("biWidth", ctypes.c_int32), ("biHeight", ctypes.c_int32),
                    ("biPlanes", ctypes.c_uint16), ("biBitCount", ctypes.c_uint16), ("biCompression", ctypes.c_uint32),
                    ("biSizeImage", ctypes.c_uint32), ("biXPelsPerMeter", ctypes.c_int32),
                    ("biYPelsPerMeter", ctypes.c_int32), ("biClrUsed", ctypes.c_uint32),
                    ("biClrImportant", ctypes.c_uint32)]

    bi = BIH()
    bi.biSize = ctypes.sizeof(BIH); bi.biWidth = W; bi.biHeight = -H
    bi.biPlanes = 1; bi.biBitCount = 32; bi.biCompression = 0
    buf = ctypes.create_string_buffer(W * H * 4)
    gdi32.GetDIBits(mdc, bmp, 0, H, buf, ctypes.byref(bi), 0)
    img = Image.frombuffer("RGBA", (W, H), buf, "raw", "BGRA", 0, 1).convert("RGB")
    gdi32.DeleteObject(bmp); gdi32.DeleteDC(mdc); user32.ReleaseDC(0, hdc)
    return img, (r.left, r.top)


def diff_pixels(a, b):
    da, db = a.tobytes(), b.tobytes()
    return sum(1 for i in range(0, len(da), 3) if da[i:i + 3] != db[i:i + 3])


def postmessage_click(hwnd, client_x, client_y):
    """PostMessage 左键点击（客户区物理坐标）。lparam 低16位=x 高16位=y。"""
    WM_LBUTTONDOWN, WM_LBUTTONUP = 0x0201, 0x0202
    MK_LBUTTON = 0x0001
    lparam = (client_y << 16) | (client_x & 0xFFFF)
    user32.PostMessageW(hwnd, WM_LBUTTONDOWN, MK_LBUTTON, lparam)
    time.sleep(0.1)
    user32.PostMessageW(hwnd, WM_LBUTTONUP, 0, lparam)


def key(vk):
    user32.keybd_event(vk, 0, 0, 0)
    user32.keybd_event(vk, 0, 2, 0)
    time.sleep(0.15)


def paste_unicode(text):
    """剪贴板粘贴中文（微信输入框/搜索框）。"""
    subprocess.run(['clip.exe'], input=text.encode('utf-16le'), check=False)
    time.sleep(0.3)
    user32.keybd_event(0x11, 0, 0, 0)
    key(0x56)
    user32.keybd_event(0x11, 0, 2, 0)
    time.sleep(0.4)


def main():
    args = sys.argv[1:]
    pid = wid = None
    for i, a in enumerate(args):
        if a == '--pid': pid = int(args[i + 1])
        if a == '--wid': wid = int(args[i + 1])
    if not pid or not wid:
        print("usage: --pid <pid> --wid <hwnd> [--click-logical x,y] [--keys ctrl+f]")
        return
    hwnd = wid

    r = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(r))
    wx, wy, ww, wh = r.left, r.top, r.right - r.left, r.bottom - r.top
    print('窗口物理 rect:', wx, wy, ww, wh)

    # ratio: 截图逻辑宽 / 物理宽（用于 frame 逻辑坐标→客户区物理坐标）
    shot = grab_cua(pid, hwnd)
    ratio = (shot.size[0] / ww) if shot else 1.0
    print('cua 截图:', shot.size if shot else None, 'ratio≈%.3f' % ratio)

    before = grab_cua(pid, hwnd)

    if '--click-logical' in args:
        lx, ly = map(int, args[args.index('--click-logical') + 1].split(','))
        cx, cy = int(lx / ratio), int(ly / ratio)
        print('PostMessage 点击客户区:', cx, cy)
        postmessage_click(hwnd, cx, cy)
        time.sleep(1.5)

    if '--keys' in args:
        ks = args[args.index('--keys') + 1]
        if ks == 'ctrl+f':
            user32.keybd_event(0x11, 0, 0, 0)
            key(0x46)
            user32.keybd_event(0x11, 0, 2, 0)
            time.sleep(1.0)
        elif ks == 'enter':
            key(0x0D)
            time.sleep(1.0)

    after = grab_cua(pid, hwnd)
    if before and after:
        print('操作后 cua 截图 diff:', diff_pixels(before, after))
        after.save(r"T:\programming\project\Hermes\cache\wx_probe_after.png")

    blt, _ = grab_bitblt(hwnd)
    blt.save(r"T:\programming\project\Hermes\cache\wx_probe_bitblt.png")
    print('BitBlt 截图尺寸:', blt.size)


if __name__ == '__main__':
    main()
