from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit
from PySide6.QtCore import Qt, QTimer, Signal, QEvent
from PySide6.QtGui import QFont

from pet_app.core.theme_config import THEMES, DEFAULT_THEME_ID, ThemeStyle
from pet_app.utils.logger import logger


class ChatPanel(QWidget):
    """Chat input panel that appears below the pet window."""

    message_sent = Signal(str)

    def __init__(self, pet_window, config=None, theme_style: ThemeStyle | None = None):
        super().__init__()
        self.pet_window = pet_window
        self.config = config
        self.theme_style = theme_style or THEMES[DEFAULT_THEME_ID]
        self.input_field = None
        self.drag_position = None
        self.last_pet_pos = None
        self.panel_height = 68
        self.input_height = 56

        self.init_ui()

        self.position_update_timer = QTimer()
        self.position_update_timer.timeout.connect(self._update_position_if_needed)
        self.position_update_timer.start(100)

        logger.info("ChatPanel initialized")

    def init_ui(self):
        """Initialize the chat panel UI."""
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
            | Qt.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)

        layout = QVBoxLayout()
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(0)

        self.input_field = QTextEdit()
        self.input_field.setPlaceholderText("和我说点什么...")
        self.input_field.setAcceptRichText(False)
        self.input_field.setFixedHeight(self.input_height)
        self.input_field.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.input_field.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.input_field.setLineWrapMode(QTextEdit.WidgetWidth)
        self.input_field.viewport().setAutoFillBackground(False)
        self.input_field.installEventFilter(self)

        self.apply_theme(self.theme_style)

        layout.addWidget(self.input_field)
        self.setLayout(layout)
        self.setGeometry(100, 200, 220, self.panel_height)

        logger.info("ChatPanel UI initialized")

    def apply_theme(self, theme_style: ThemeStyle):
        """Apply the selected theme to the chat input."""
        self.theme_style = theme_style

        font = QFont(theme_style.font_family, theme_style.input_font_size)
        font.setFamilies([theme_style.font_family, theme_style.font_fallback, "Segoe UI"])
        font.setWeight(QFont.Weight.Normal)
        try:
            font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias | QFont.StyleStrategy.PreferQuality)
        except AttributeError:
            font.setStyleStrategy(QFont.PreferAntialias)

        self.input_field.setFont(font)
        self.input_field.setStyleSheet(f"""
            QTextEdit {{
                background-color: {theme_style.input_background};
                border: 1.5px solid {theme_style.input_border};
                border-radius: {theme_style.input_radius}px;
                padding: 10px 14px;
                color: {theme_style.input_text};
                selection-background-color: {theme_style.input_selection};
                selection-color: {theme_style.input_text};
                letter-spacing: 0;
            }}
            QTextEdit:focus {{
                border: 1.5px solid {theme_style.input_focus_border};
                background-color: {theme_style.input_background};
            }}
        """)

    def set_theme(self, theme_style: ThemeStyle):
        """Switch chat input theme at runtime."""
        self.apply_theme(theme_style)
        self.update()

    def eventFilter(self, obj, event):
        """Handle key events in the input field."""
        if obj == self.input_field and event.type() == QEvent.KeyPress:
            from PySide6.QtGui import QKeyEvent

            if isinstance(event, QKeyEvent):
                if event.key() == Qt.Key_Return and not (event.modifiers() & Qt.ShiftModifier):
                    self.send_message()
                    return True

        return super().eventFilter(obj, event)

    def send_message(self):
        """Send the message from the input field."""
        text = self.input_field.toPlainText().strip()

        if not text:
            logger.debug("Empty message, not sending")
            return

        logger.info(f"Sending message: {text[:50]}...")
        self.message_sent.emit(text)

        self.input_field.clear()
        self.input_field.setFocus()
        self.input_field.setFixedHeight(self.input_height)

    def update_position_from_pet(self):
        """Update chat panel position to be directly below pet window."""
        if not self.pet_window or not self.pet_window.isVisible():
            return

        pet_pos = self.pet_window.pos()
        pet_width = self.pet_window.width()
        pet_height = self.pet_window.height()

        panel_x = pet_pos.x()
        panel_y = pet_pos.y() + pet_height
        self.setGeometry(panel_x, panel_y, pet_width, self.panel_height)

        self.last_pet_pos = pet_pos

    def _update_position_if_needed(self):
        """Check if pet position changed and update panel position."""
        if not self.isVisible() or not self.pet_window:
            return

        current_pet_pos = self.pet_window.pos()
        if self.last_pet_pos is None or self.last_pet_pos != current_pet_pos:
            self.update_position_from_pet()

    def show_panel(self):
        """Show the chat panel."""
        logger.info("Showing chat panel")
        self.update_position_from_pet()
        self.show()
        self.input_field.setFocus()

    def hide_panel(self):
        """Hide the chat panel."""
        logger.info("Hiding chat panel")
        self.hide()

    def on_pet_moved(self):
        """Called when pet window is moved."""
        if self.isVisible():
            self.update_position_from_pet()
