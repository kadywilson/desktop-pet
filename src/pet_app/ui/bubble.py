from PySide6.QtWidgets import QLabel, QWidget, QVBoxLayout
from PySide6.QtCore import Qt, Signal, QRectF
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen

from pet_app.core.theme_config import THEMES, DEFAULT_THEME_ID, ThemeStyle
from pet_app.utils.logger import logger


def _color_from_qss(value: str) -> QColor:
    """Parse #RRGGBB or rgba(r, g, b, a) strings for QPainter."""
    text = (value or "").strip()
    if text.startswith("rgba(") and text.endswith(")"):
        parts = [part.strip() for part in text[5:-1].split(",")]
        if len(parts) == 4:
            return QColor(int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3]))
    return QColor(text)


class SpeechBubble(QWidget):
    """Speech bubble window shown above the pet - clickable to hide."""
    
    bubble_clicked = Signal()  # Signal when bubble is clicked
    reset_expression = Signal()  # Signal to reset pet to default expression

    def __init__(self, parent=None, config=None, theme_style: ThemeStyle | None = None):
        super().__init__(parent)
        self.pet_window = parent
        self.config = config
        self.theme_style = theme_style or THEMES[DEFAULT_THEME_ID]
        self._tail_height = 16
        self.init_ui()

    def init_ui(self):
        """Initialize the speech bubble UI."""
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAutoFillBackground(False)

        layout = QVBoxLayout()
        layout.setContentsMargins(22, 18, 22, 18 + self._tail_height)
        layout.setSpacing(0)

        self.label = QLabel()
        self.label.setAttribute(Qt.WA_TranslucentBackground)
        self.label.setWordWrap(True)
        self.label.setMinimumWidth(150)
        self.label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.label.setCursor(Qt.PointingHandCursor)

        layout.addWidget(self.label)
        self.setLayout(layout)
        self.apply_theme(self.theme_style)

        logger.info("Speech bubble initialized")

    def _bubble_path(self, rect: QRectF) -> QPainterPath:
        radius = float(self.theme_style.bubble_radius)
        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)

        tail_center = rect.center().x()
        tail_half_width = 15.0
        tail_tip_y = rect.bottom() + self._tail_height
        path.moveTo(tail_center - tail_half_width, rect.bottom() - 1)
        path.lineTo(tail_center, tail_tip_y)
        path.lineTo(tail_center + tail_half_width, rect.bottom() - 1)
        path.closeSubpath()
        return path

    def paintEvent(self, event):
        """Paint a translucent rounded bubble behind the text."""
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)

        body_rect = QRectF(5, 5, self.width() - 10, self.height() - self._tail_height - 10)
        path = self._bubble_path(body_rect)

        shadow_path = path.translated(0, 4)
        painter.fillPath(shadow_path, _color_from_qss(self.theme_style.bubble_shadow))

        painter.fillPath(path, _color_from_qss(self.theme_style.bubble_background))
        pen = QPen(_color_from_qss(self.theme_style.bubble_border))
        pen.setWidthF(1.5)
        painter.setPen(pen)
        painter.drawPath(path)
        painter.end()

    def apply_theme(self, theme_style: ThemeStyle):
        """Apply theme colors and font without rebuilding the bubble."""
        self.theme_style = theme_style

        font = QFont(theme_style.font_family, theme_style.bubble_font_size)
        font.setFamilies([theme_style.font_family, theme_style.font_fallback, "Segoe UI"])
        font.setWeight(
            QFont.Weight.Medium
            if theme_style.bubble_font_weight >= 500
            else QFont.Weight.Normal
        )
        try:
            font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias | QFont.StyleStrategy.PreferQuality)
        except AttributeError:
            font.setStyleStrategy(QFont.PreferAntialias)

        self.label.setFont(font)
        self.label.setMaximumWidth(theme_style.bubble_max_width)
        self.label.setStyleSheet(
            f"""
            QLabel {{
                background: transparent;
                border: none;
                color: {theme_style.bubble_text};
                padding: 0;
                letter-spacing: 0;
            }}
            """
        )
        self.update()

    def show_bubble(self, text, duration_ms=0):
        """
        Show the bubble with the given text.
        
        Args:
            text: Bubble text
            duration_ms: Auto-hide duration (0 = no auto-hide, click to dismiss)
        """
        logger.info(f"show_bubble called with text: {text}")
        self.label.setText(text)
        self.adjustSize()

        if self.pet_window:
            pet_pos = self.pet_window.pos()
            pet_size = self.pet_window.size()
            self_size = self.size()

            # Use bubble_offset from config if available
            offset_x = 0
            offset_y = -100
            if self.config:
                offset_x = self.config.bubble_offset.x
                offset_y = self.config.bubble_offset.y

            x = pet_pos.x() + (pet_size.width() - self_size.width()) // 2 + offset_x
            y = pet_pos.y() + offset_y

            logger.info(f"Positioning bubble at ({x}, {y}), size: {self_size.width()}x{self_size.height()}")
            self.move(x, y)

        logger.info(f"Showing bubble, calling show()")
        self.show()
        self.raise_()
        self.activateWindow()

        logger.info(f"Bubble will persist until clicked (duration_ms={duration_ms})")

    def mousePressEvent(self, event):
        """Handle mouse press to hide bubble."""
        if event.button() == Qt.LeftButton:
            logger.info("Bubble clicked, hiding and resetting expression to default")
            self.hide_bubble()
            self.reset_expression.emit()
            self.bubble_clicked.emit()

    def enterEvent(self, event):
        """Handle mouse enter to show hand cursor."""
        self.setCursor(Qt.PointingHandCursor)

    def leaveEvent(self, event):
        """Handle mouse leave."""
        self.setCursor(Qt.ArrowCursor)

    def hide_bubble(self):
        """Hide the bubble."""
        logger.info("Hiding bubble")
        self.hide()
