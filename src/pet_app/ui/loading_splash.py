"""Startup loading splash window."""

import sys
import ctypes

from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QColor, QFont, QPainter, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsDropShadowEffect,
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from pet_app.utils.paths import get_app_icon_path_png, get_app_icon_path_ico


class PulseIcon(QWidget):
    """Icon with a soft pulse ring for the loading splash."""

    def __init__(self, pixmap: QPixmap, parent=None):
        super().__init__(parent)
        self.pixmap = pixmap
        self.phase = 0
        self.setFixedSize(80, 80)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(90)

    def _tick(self):
        self.phase = (self.phase + 1) % 20
        self.update()

    def paintEvent(self, event):
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        pulse = abs(self.phase - 10) / 10
        alpha = int(70 + (1 - pulse) * 75)
        inset = int(3 + pulse * 4)

        painter.setPen(QColor(175, 198, 226, alpha))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(inset, inset, self.width() - inset * 2, self.height() - inset * 2)

        if not self.pixmap.isNull():
            target_size = QSize(58, 58)
            scaled = self.pixmap.scaled(
                target_size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)

        painter.end()


class LoadingSplash(QWidget):
    """Milk Center startup splash screen."""

    def __init__(self):
        super().__init__()
        self.status_label = None
        self.init_ui()

    def init_ui(self):
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(380, 300)

        root_layout = QVBoxLayout()
        root_layout.setContentsMargins(20, 20, 20, 20)
        root_layout.setSpacing(0)

        card = QFrame()
        card.setObjectName("loadingCard")
        card.setFixedSize(340, 260)
        card.setStyleSheet(
            """
            QFrame#loadingCard {
                background-color: rgba(255, 255, 255, 232);
                border: 1.5px solid rgba(175, 198, 226, 230);
                border-radius: 26px;
            }
            """
        )

        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(42)
        shadow.setOffset(0, 18)
        shadow.setColor(QColor(100, 130, 168, 46))
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(28, 26, 28, 24)
        card_layout.setSpacing(12)
        card_layout.setAlignment(Qt.AlignCenter)

        icon = PulseIcon(self._load_icon_pixmap())
        card_layout.addWidget(icon, 0, Qt.AlignHCenter)

        title = QLabel("加载中")
        title_font = QFont("Microsoft YaHei UI", 15)
        title_font.setFamilies(["Microsoft YaHei UI", "Microsoft YaHei", "Segoe UI"])
        title_font.setWeight(QFont.Weight.DemiBold)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #24292F; background: transparent; letter-spacing: 0;")
        card_layout.addWidget(title)

        self.status_label = QLabel("正在启动桌宠...")
        status_font = QFont("Microsoft YaHei UI", 10)
        status_font.setFamilies(["Microsoft YaHei UI", "Microsoft YaHei", "Segoe UI"])
        self.status_label.setFont(status_font)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: #687381; background: transparent; letter-spacing: 0;")
        card_layout.addWidget(self.status_label)

        progress = QProgressBar()
        progress.setRange(0, 0)
        progress.setTextVisible(False)
        progress.setFixedSize(230, 7)
        progress.setStyleSheet(
            """
            QProgressBar {
                background-color: rgba(175, 198, 226, 58);
                border: none;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background-color: #7AA7D8;
                border-radius: 3px;
                width: 48px;
            }
            """
        )
        card_layout.addWidget(progress, 0, Qt.AlignHCenter)

        card.setLayout(card_layout)
        root_layout.addWidget(card, 0, Qt.AlignCenter)
        self.setLayout(root_layout)
        self.center_on_screen()

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, self.force_top)

    def _load_icon_pixmap(self) -> QPixmap:
        icon_path = get_app_icon_path_png() or get_app_icon_path_ico()
        if icon_path:
            pixmap = QPixmap(str(icon_path))
            if not pixmap.isNull():
                return pixmap

        pixmap = QPixmap(58, 58)
        pixmap.fill(QColor(0, 0, 0, 0))
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setBrush(QColor(122, 167, 216))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(4, 4, 50, 50)
        painter.end()
        return pixmap

    def center_on_screen(self):
        screen = QApplication.primaryScreen()
        if not screen:
            return
        geometry = screen.availableGeometry()
        x = geometry.center().x() - self.width() // 2
        y = geometry.center().y() - self.height() // 2
        self.move(x, y)

    def set_status(self, text: str):
        if self.status_label:
            self.status_label.setText(text)
        self.raise_()
        self.activateWindow()
        self.force_top()

    def force_top(self):
        """Keep the splash above normal windows, matching the desktop pet behavior."""
        self.raise_()
        if sys.platform != "win32":
            return

        try:
            hwnd = int(self.winId())
            hwnd_topmost = -1
            swp_nosize = 0x0001
            swp_nomove = 0x0002
            swp_showwindow = 0x0040
            ctypes.windll.user32.SetWindowPos(
                hwnd,
                hwnd_topmost,
                0,
                0,
                0,
                0,
                swp_nomove | swp_nosize | swp_showwindow,
            )
        except Exception:
            # Qt's WindowStaysOnTopHint remains the fallback if native pinning fails.
            return
