import threading
import time
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QClipboard

# 全局锁，防止多线程访问冲突
_clipboard_read_lock = threading.Lock()

def safe_read_clipboard_qt(retry=5, delay=0.1):
    """
    从剪贴板安全读取文本，专为 PyQt5 GUI 主线程设计，支持自动重试。
    """
    # 必须确保 QApplication 是在主线程创建的
    app = QApplication.instance()
    if app is None:
        raise RuntimeError("QApplication instance not found. Must be called from within a PyQt5 GUI application.")

    clipboard: QClipboard = app.clipboard()

    for attempt in range(retry):
        with _clipboard_read_lock:
            try:
                text = clipboard.text()
                return text
            except Exception as e:
                print(f"[Retry {attempt+1}] 读取剪贴板失败: {e}")
                time.sleep(delay)

    print("读取剪贴板失败：超过最大重试次数")
    return ""
