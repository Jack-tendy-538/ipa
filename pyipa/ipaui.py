import win32com.client
import subprocess
from . import avtk

# TODO： 获取前台窗口进程句柄
def get_foreground_window_process_handle():
    shell = win32com.client.Dispatch("WScript.Shell")
    shell.AppActivate(win32com.client.Dispatch("WScript.Shell").AppActivate)
    hwnd = win32com.client.Dispatch("user32").GetForegroundWindow()
    pid = win32com.client.Dispatch("user32").GetWindowThreadProcessId(hwnd)[1]
    process_handle = win32com.client.Dispatch("kernel32").OpenProcess(0x1F0FFF, False, pid)
    return process_handle

# TODO： 如果不是PowerPoint进程或者不是放映状态，退出程序
def ensure_powerpoint_process():
    process_handle = get_foreground_window_process_handle()
    process_name = avtk.get_process_name(process_handle)
    if process_name.lower() != "powerpnt.exe":
        raise Exception("当前前台窗口不是PowerPoint进程。")

    if not PPTObj.SlideShowWindows:
        raise Exception("当前PowerPoint没有处于放映状态。")

# TODO： 获取PowerPoint应用程序对象
def get_powerpoint_app():
    ensure_powerpoint_process()
    powerpoint_app = win32com.client.Dispatch("PowerPoint.Application")
    return powerpoint_app

# TODO： 用avtk创建窗口以与用户交互
def create_interactive_window(title, width, height):
    app = avtk.App()
    window = app.create_window(title, width, height)
    return app, window

PPTObj = get_powerpoint_app()

def checkIfPPTLockedOrReadOnly():
    try:
        presentation = PPTObj.ActivePresentation
        if presentation.ReadOnly:
            return True
        else:
            return False
    except Exception:
        return True

def Unlock():
    # 尝试解除PowerPoint的只读状态
    try:
        presentation = PPTObj.ActivePresentation
        if presentation.ReadOnly:
            presentation.ReadOnly = False
    except Exception as e:
        print(f"无法解除只读状态: {e}")
    # 尝试关闭保护视图
    try:
        subprocess.run(["powershell", "-Command", "Set-ItemProperty -Path 'HKCU:\\Software\\Microsoft\\Office\\16.0\\PowerPoint\\Security' -Name 'EnableProtectedView' -Value 0"], check=True)
    except Exception as e:
        print(f"无法关闭保护视图: {e}")

def SendKeysToPPT(keys):
    ensure_powerpoint_process()
    shell = win32com.client.Dispatch("WScript.Shell")
    shell.AppActivate("Microsoft PowerPoint")
    shell.SendKeys(keys)

def SendPageDownToPPT():
    SendKeysToPPT("{PGDN}")

def SendPageUpToPPT():
    SendKeysToPPT("{PGUP}")

def SendEscToPPT():
    SendKeysToPPT("{ESC}")

def ToogleArrowStatusToPPT(status):
    # 将箭头状态切换为指定状态
    # status: arrow / pen / eraser
    PPTObj.SlideShowWindows(1).View.PointerType = {
        "arrow": 1,
        "pen": 2,
        "eraser": 3
    }.get(status, 1)

def ClearAllInkInPPT():
    PPTObj.SlideShowWindows(1).View.EraseAllInk()

def GetCurrentSlideIndex():
    return PPTObj.SlideShowWindows(1).View.Slide.SlideIndex

def SendViewAllSlidesToPPT():
    SendKeysToPPT("G")

# avtk窗口示例
def makeLockedAvtkWindow():
    app, window = create_interactive_window("PPT已锁定", 400, 200)
    label = app.create_label(window, "检测到当前PPT处于只读或保护视图状态，请解除锁定后继续操作。", 20, 50)
    button = app.create_button(window, "我已解除锁定", 150, 120)
    def on_button_click():
        if not checkIfPPTLockedOrReadOnly():
            app.close_window(window)
        else:
            app.update_label(label, "PPT仍然处于只读或保护视图状态，请继续解除锁定。")
    app.set_button_callback(button, on_button_click)
    app.run()

def makeMainWindow():
    # 显示ppt控制面板
    app, window = create_interactive_window("PPT控制面板", 400, 300)
    # 所有元素在同一排水平居中
    btn_page_down = app.create_button(window, "下一页", 50, 50)
    btn_page_up = app.create_button(window, "上一页", 150, 50)
    btn_esc = app.create_button(window, "退出放映", 250, 50)
    btn_view_all = app.create_button(window, "查看所有幻灯片", 50, 100)
    btn_arrow = app.create_button(window, "切换到箭头", 150, 100)
    btn_pen = app.create_button(window, "切换到画笔", 250, 100)
    btn_eraser = app.create_button(window, "切换到橡皮擦", 50, 150)
    btn_clear_ink = app.create_button(window, "清除所有墨迹", 150, 150)
    label_slide_index = app.create_label(window, f"当前幻灯片索引: {GetCurrentSlideIndex()}", 50, 200)
    def update_slide_index_label():
        app.update_label(label_slide_index, f"当前幻灯片索引: {GetCurrentSlideIndex()}")
    app.set_button_callback(btn_page_down, lambda: [SendPageDownToPPT(), update_slide_index_label()])
    app.set_button_callback(btn_page_up, lambda: [SendPageUpToPPT(), update_slide_index_label()])
    app.set_button_callback(btn_esc, SendEscToPPT)
    app.set_button_callback(btn_view_all, SendViewAllSlidesToPPT)
    app.set_button_callback(btn_arrow, lambda: ToogleArrowStatusToPPT("arrow"))
    app.set_button_callback(btn_pen, lambda: ToogleArrowStatusToPPT("pen"))
    app.set_button_callback(btn_eraser, lambda: ToogleArrowStatusToPPT("eraser"))
    app.set_button_callback(btn_clear_ink, ClearAllInkInPPT)
    app.run()

def runPPTControlPanel():
    if checkIfPPTLockedOrReadOnly():
        makeLockedAvtkWindow()
    makeMainWindow()

if __name__ == "__main__":
    runPPTControlPanel()