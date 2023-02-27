
import win32gui
import win32con

def maximize_postprocessor():
    """Maximize all Adams PostProcessor windows
    """
    window_list = []
    win32gui.EnumWindows(lambda h, _ctx : window_list.append(h) if win32gui.IsWindowVisible(h) else None, None)
    for hwnd in (h for h in window_list if 'Adams PostProcessor' in win32gui.GetWindowText(h)):
        win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
