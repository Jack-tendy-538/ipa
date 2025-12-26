# ipaui.py - 重写后的 PowerPoint 控制与 avtk 交互示例
# 依赖：pywin32, psutil, win32com, 以及你的 avtk 模块（AvTk 风格）
import time
import threading
from typing import Optional, Tuple

import psutil
import win32gui
import win32process
import win32con
import win32api
import pythoncom
import win32com.client

# 假定 avtk 提供 AvTk() / AvWindow 风格接口（参见你项目中的 avtk.py）
from . import avtk

# 全局缓存的 PowerPoint COM 对象（惰性初始化）
_PPT_APP = None


def get_foreground_process_info() -> Optional[Tuple[int, str, int]]:
    """
    返回 (pid, process_name, hwnd) 或 None（如果无法获取）
    使用 win32gui + win32process + psutil 以获得可靠的进程名。
    """
    try:
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return None
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        try:
            proc = psutil.Process(pid)
            name = proc.name()
        except Exception:
            name = None
        return pid, name, hwnd
    except Exception:
        return None


def is_foreground_powerpoint() -> bool:
    info = get_foreground_process_info()
    if not info:
        return False
    _, name, _ = info
    if not name:
        return False
    return name.lower() in ("powerpnt.exe", "powerpoint.exe")


def get_powerpoint_app() -> Optional[object]:
    """
    惰性获取 PowerPoint.Application COM 对象并缓存。
    注意：调用 COM 接口前应在当前线程调用 pythoncom.CoInitialize()（如果在新线程使用）。
    """
    global _PPT_APP
    if _PPT_APP is not None:
        return _PPT_APP
    try:
        # 确保 COM 已初始化（如果此函数在非主线程调用）
        pythoncom.CoInitialize()
        _PPT_APP = win32com.client.Dispatch("PowerPoint.Application")
        return _PPT_APP
    except Exception as e:
        # 无 PowerPoint 或 COM 调用失败
        print("无法连接到 PowerPoint:", e)
        return None


def ensure_powerpoint_in_slideshow() -> object:
    """
    获取 PowerPoint 应用对象并确保当前有处于放映状态的窗口。
    返回 PPT 应用对象（成功），否则抛出异常。
    """
    ppt = get_powerpoint_app()
    if ppt is None:
        raise RuntimeError("未找到 PowerPoint 应用.")
    try:
        # SlideShowWindows 是集合，Count 属性表示数量
        if getattr(ppt.SlideShowWindows, "Count", 0) < 1:
            raise RuntimeError("当前没有处于放映状态的幻灯片放映窗口.")
        return ppt
    except Exception as e:
        raise RuntimeError(f"检查放映状态失败: {e}")


def checkIfPPTLockedOrReadOnly() -> bool:
    """
    检查当前 ActivePresentation 是否只读（或无法访问）。
    返回 True 表示被锁定/只读/不可访问。
    """
    ppt = get_powerpoint_app()
    if not ppt:
        return True
    try:
        pres = ppt.ActivePresentation
        # Presentation 对象通常有 ReadOnly 属性（如果不存在，可根据需要调整）
        return bool(getattr(pres, "ReadOnly", False))
    except Exception:
        # 无法获取 Presentation（可能没有打开演示文稿）
        return True


def Unlock():
    """
    尝试解除只读（注：许多只读/保护视图问题无法通过 COM 在外部强制解除）。
    这里我们尽量尝试一些安全操作，否则提示用户手动解除。
    """
    ppt = get_powerpoint_app()
    if not ppt:
        print("未连接 PowerPoint，无法解除锁定。")
        return False
    try:
        pres = ppt.ActivePresentation
        if getattr(pres, "ReadOnly", False):
            # 尝试保存为新的文件（提示用户选择路径）或提示用户手动解除保护
            print("当前演示文稿为只读。建议另存为或在 PowerPoint 中手动解除保护。")
            return False
        # 如果不是 ReadOnly，则认为已解除
        return True
    except Exception as e:
        print("尝试解除只读时出错:", e)
        return False


# 控制放映的辅助函数（优先使用 PowerPoint COM API而不是 SendKeys）
def _get_slideshow_view(ppt):
    """返回第一个放映窗口的 SlideShowView"""
    try:
        # SlideShowWindows 是 1 基的集合对象（COM 接口）
        if ppt.SlideShowWindows.Count >= 1:
            ssw = ppt.SlideShowWindows(1)
            return ssw.View
    except Exception:
        pass
    return None


def SendPageDownToPPT():
    ppt = ensure_powerpoint_in_slideshow()
    view = _get_slideshow_view(ppt)
    if view is not None:
        try:
            view.Next()  # 使用 COM 的 Next 方法
        except Exception:
            # 回退到 SendKeys（不优先）
            SendKeysToPPT("{PGDN}")


def SendPageUpToPPT():
    ppt = ensure_powerpoint_in_slideshow()
    view = _get_slideshow_view(ppt)
    if view is not None:
        try:
            view.Previous()
        except Exception:
            SendKeysToPPT("{PGUP}")


def SendEscToPPT():
    ppt = ensure_powerpoint_in_slideshow()
    view = _get_slideshow_view(ppt)
    if view is not None:
        try:
            view.Exit()
        except Exception:
            SendKeysToPPT("{ESC}")


def SendKeysToPPT(keys: str):
    """
    作为最后手段用 SendKeys。要求 PowerPoint 窗口为前台。
    """
    info = get_foreground_process_info()
    if not info or info[1] is None or info[1].lower() not in ("powerpnt.exe", "powerpoint.exe"):
        # 尝试激活 PowerPoint 主窗口（取第一个 PowerPoint 进程）
        for p in psutil.process_iter(['name', 'pid']):
            if p.info['name'] and p.info['name'].lower() in ("powerpnt.exe", "powerpoint.exe"):
                try:
                    # 找到进程对应的主窗口（非常简化的方式）
                    hwnds = []
                    def enum_cb(hwnd, extra):
                        _, pid = win32process.GetWindowThreadProcessId(hwnd)
                        if pid == p.info['pid'] and win32gui.IsWindowVisible(hwnd):
                            hwnds.append(hwnd)
                    win32gui.EnumWindows(enum_cb, None)
                    if hwnds:
                        win32gui.SetForegroundWindow(hwnds[0])
                        break
                except Exception:
                    pass
    try:
        shell = win32com.client.Dispatch("WScript.Shell")
        shell.SendKeys(keys)
    except Exception as e:
        print("SendKeys 失败:", e)


def ToogleArrowStatusToPPT(status: str):
    """
    status: "arrow" / "pen" / "eraser"
    使用 PowerPoint 常量设置 PointerType。
    """
    ppt = ensure_powerpoint_in_slideshow()
    view = _get_slideshow_view(ppt)
    if view is None:
        return
    try:
        c = win32com.client.constants
        mapping = {
            "arrow": 1,   # 常数 ppSlideShowPointerNone/Arrow 等（1通常是箭头）
            "pen": 2,
            "eraser": 3
        }
        view.PointerType = mapping.get(status, 1)
    except Exception as e:
        print("切换指针状态失败:", e)


def ClearAllInkInPPT():
    try:
        ppt = ensure_powerpoint_in_slideshow()
        view = _get_slideshow_view(ppt)
        if view:
            view.EraseAllInk()
    except Exception as e:
        print("清除墨迹失败:", e)


def GetCurrentSlideIndex() -> int:
    try:
        ppt = ensure_powerpoint_in_slideshow()
        view = _get_slideshow_view(ppt)
        if view and view.Slide is not None:
            return int(view.Slide.SlideIndex)
    except Exception:
        pass
    return -1


# ------- avtk 界面（按 AvTk 接口写法） -------
def create_interactive_window(title: str, width: int, height: int):
    """
    使用 avtk 提供的 AvTk / AvWindow 接口构建窗口并返回 (window, toolkit)
    假设 avtk.AvTk() 返回 AvWindow 实例（按你仓库的 avtk.py）。
    """
    # 这里直接返回 AvWindow 实例作为 app 的唯一对象
    win = avtk.AvTk()  # 或 avtk.AvWindow() 视你的实现而定
    win.title = title
    win.width = width
    win.height = height
    return win  # 直接返回窗口对象（与旧接口不同）


# 示例窗口：锁定提示窗口（使用 avtk API）
def makeLockedAvtkWindow():
    win = create_interactive_window("PPT已锁定", 400, 200)
    lbl = win.Label("检测到当前PPT处于只读或保护视图状态，请解除锁定后继续操作。").pack()
    def on_ok():
        if not checkIfPPTLockedOrReadOnly():
            # 关闭窗口（avtk 的 close 方法视具体实现而定）
            try:
                win.destroy()
            except Exception:
                pass
        else:
            # 更新文本
            try:
                lbl.set_text("PPT仍然处于只读或保护视图状态，请继续解除锁定。")
            except Exception:
                pass
    btn = win.Button("我已解除锁定", command=on_ok).pack()
    win.mainloop()


def makeMainWindow():
    win = create_interactive_window("PPT控制面板", 400, 300)
    # 使用 avtk 的 Button/Label 接口
    lbl_index = win.Label(f"当前幻灯片索引: {GetCurrentSlideIndex()}").pack()

    def update_slide_label():
        try:
            lbl_index.set_text(f"当前幻灯片索引: {GetCurrentSlideIndex()}")
        except Exception:
            pass

    win.Button("下一页", command=lambda: (SendPageDownToPPT(), update_slide_label())).pack()
    win.Button("上一页", command=lambda: (SendPageUpToPPT(), update_slide_label())).pack()
    win.Button("退出放映", command=SendEscToPPT).pack()
    win.Button("查看所有幻灯片", command=lambda: SendKeysToPPT("g")).pack()
    win.Button("切换到箭头", command=lambda: ToogleArrowStatusToPPT("arrow")).pack()
    win.Button("切换到画笔", command=lambda: ToogleArrowStatusToPPT("pen")).pack()
    win.Button("切换到橡皮擦", command=lambda: ToogleArrowStatusToPPT("eraser")).pack()
    win.Button("清除所有墨迹", command=ClearAllInkInPPT).pack()

    win.mainloop()


def runPPTControlPanel():
    if checkIfPPTLockedOrReadOnly():
        makeLockedAvtkWindow()
    else:
        makeMainWindow()


if __name__ == "__main__":
    runPPTControlPanel()