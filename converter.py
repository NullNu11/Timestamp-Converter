import sys
from importlib.resources import contents

import pytz
import pyperclip
import re
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QSystemTrayIcon
)
from PyQt5.QtCore import QTimer, Qt, QPoint, QEvent
from PyQt5.QtGui import QIcon

import readFromClipboard


class TimestampConverter(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("划词时间戳转换工具")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.resize(400, 200)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.clipboard_content = ""
        self.dragging = False
        self.mouse_in = False
        self.is_docked = False
        self.edge_margin = 5  # 收缩时保留 5px

        # 输入框
        self.input_label = QLabel("输入时间戳 / 日期：")
        self.input_edit = QLineEdit()
        self.result_label = QLabel("转换结果：")
        self.result_display = QLabel("")
        self.result_display.setTextInteractionFlags(Qt.TextSelectableByMouse)

        # 时区选择
        self.timezone_box = QComboBox()
        self.timezone_box.addItems(pytz.all_timezones)
        self.timezone_box.setCurrentText("Asia/Shanghai")

        # 转换按钮
        self.convert_button = QPushButton("手动转换")
        self.convert_button.clicked.connect(self.convert)

        self.layout.addWidget(self.input_label)
        self.layout.addWidget(self.input_edit)
        self.layout.addWidget(QLabel("选择时区："))
        self.layout.addWidget(self.timezone_box)
        self.layout.addWidget(self.convert_button)
        self.layout.addWidget(self.result_label)
        self.layout.addWidget(self.result_display)

        # 自动监听剪贴板
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_clipboard)
        self.timer.start(1000)

        # 鼠标检测收缩展开
        self.hover_timer = QTimer(self)
        self.hover_timer.timeout.connect(self.check_mouse_position)
        self.hover_timer.start(300)

        self.installEventFilter(self)

        # 在 __init__ 里面添加
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("C:\\Users\\Eric\\Pictures\\time.png"))  # 要指定一个图标，不然不会显示
        self.tray_icon.setVisible(True)

    def check_clipboard(self):
        #content = pyperclip.paste().strip()
        content = readFromClipboard.safe_read_clipboard_qt()
        if content != self.clipboard_content:
            self.clipboard_content = content
            self.input_edit.setText(content)
            self.convert()

    def convert(self):
        tz = pytz.timezone(self.timezone_box.currentText())
        text = self.input_edit.text().strip()
        result = ""
        try:
            if re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$", text):
                dt = datetime.strptime(text, "%Y-%m-%d %H:%M:%S")
                dt = tz.localize(dt)
                timestamp = int(dt.timestamp())
                result = f"秒：{timestamp} | 毫秒：{timestamp * 1000}"
            elif re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", text):
                dt = datetime.strptime(text, "%Y-%m-%dT%H:%M:%S")
                dt = tz.localize(dt)
                timestamp = int(dt.timestamp())
                result = f"秒：{timestamp} | 毫秒：{timestamp * 1000}"
            elif re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$", text):
                dt = datetime.strptime(text, "%Y-%m-%dT%H:%M")
                dt = tz.localize(dt)
                timestamp = int(dt.timestamp())
                result = f"秒：{timestamp} | 毫秒：{timestamp * 1000}"
            elif re.match(r"^\d{10,13}$", text):
                if len(text) == 13:
                    ts = int(text) / 1000
                else:
                    ts = int(text)
                dt = datetime.fromtimestamp(ts, tz)
                result = dt.strftime("%Y-%m-%d %H:%M:%S")
            else:
                result = "无法识别的格式"
        except Exception as e:
            result = f"错误: {str(e)}"
        self.result_display.setText(result)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.dragging:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.check_dock()

    def check_dock(self):
        screen = QApplication.desktop().screenGeometry()
        x, y = self.x(), self.y()

        if x <= 10:
            self.move(0, y)
            self.is_docked = 'left'
        elif x + self.width() >= screen.width() - 10:
            self.move(screen.width() - self.width(), y)
            self.is_docked = 'right'
        else:
            self.is_docked = False

    def check_mouse_position(self):
        cursor_pos = QApplication.desktop().cursor().pos()
        window_rect = self.geometry()

        if self.is_docked and not window_rect.contains(cursor_pos):
            if self.is_docked == 'left':
                self.move(-self.width() + self.edge_margin, self.y())
            elif self.is_docked == 'right':
                screen = QApplication.desktop().screenGeometry()
                self.move(screen.width() - self.edge_margin, self.y())
        elif self.is_docked:
            if self.is_docked == 'left':
                self.move(0, self.y())
            elif self.is_docked == 'right':
                screen = QApplication.desktop().screenGeometry()
                self.move(screen.width() - self.width(), self.y())

    def eventFilter(self, obj, event):
        if event.type() == QEvent.WindowDeactivate:
            self.check_dock()
        return super().eventFilter(obj, event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TimestampConverter()
    window.show()
    sys.exit(app.exec_())
