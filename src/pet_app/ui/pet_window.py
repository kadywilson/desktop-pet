from PySide6.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget, QApplication
from PySide6.QtCore import Qt, QPoint, QSize, QTimer, QRect, QThread, Signal, QRunnable, QThreadPool
from PySide6.QtGui import QPixmap, QColor, QPainter, QIcon, QCursor

from pet_app.core.character import CharacterLoader
from pet_app.core.theme_config import THEMES, DEFAULT_THEME_ID, ThemeStyle
from pet_app.utils.logger import logger
from pet_app.ui.bubble import SpeechBubble


# Bubble text for each expression (fallback when no AI)
EXPRESSION_BUBBLE_TEXT = {
    "default": "你点我干嘛！",
    "happy": "哼哼，心情不错。",
    "annoyed": "不要一直戳我啦。",
    "upset": "今天有点不开心。"
}

# Expression cycle order
EXPRESSION_CYCLE = ["default", "happy", "annoyed", "upset"]


class AIWorker(QRunnable):
    """Worker thread for AI requests."""
    
    def __init__(self, ai_callback, persona: str):
        super().__init__()
        self.ai_callback = ai_callback
        self.persona = persona
    
    def run(self):
        """Run AI request in background thread."""
        try:
            response = self.ai_callback(self.persona)
        except Exception as e:
            logger.error(f"AI worker error: {e}")


class PetWindow(QMainWindow):
    """Main window for the desktop pet."""
    
    ai_response_signal = Signal(dict)  # Signal for AI response
    reset_to_default_signal = Signal()  # Signal to reset to default
    context_menu_requested = Signal(QPoint)  # Signal for right-click context menu

    def __init__(
        self,
        character_loader: CharacterLoader = None,
        conversation_service=None,
        theme_style: ThemeStyle | None = None,
    ):
        super().__init__()
        self.character_loader = character_loader or CharacterLoader()
        self.config = self.character_loader.get_config()
        self.conversation_service = conversation_service
        self.theme_style = theme_style or THEMES[DEFAULT_THEME_ID]

        self.pet_image_label = None
        self.bubble = None
        self.drag_position = None
        self.current_expression = self.config.default_expression
        self.expression_index = 0
        self.bubble_visible = False
        self.chat_panel = None  # Will be set by app after creation

        self.thread_pool = QThreadPool()

        # Connect AI response signal
        self.ai_response_signal.connect(self.on_ai_response)
        self.reset_to_default_signal.connect(self.reset_to_default_expression)

        self.init_ui()

    def init_ui(self):
        """Initialize the pet window UI."""
        self.setWindowTitle("Desktop Pet")
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)

        central_widget = QWidget()
        central_widget.setAttribute(Qt.WA_TranslucentBackground)
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.pet_image_label = QLabel()
        self.pet_image_label.setAlignment(Qt.AlignCenter)
        self.pet_image_label.setCursor(Qt.OpenHandCursor)
        self.pet_image_label.setAttribute(Qt.WA_TranslucentBackground)
        
        # Set label size from config
        label_width = self.config.image_size.width
        label_height = self.config.image_size.height
        self.pet_image_label.setFixedSize(label_width, label_height)

        self.load_and_display_expression(self.current_expression)

        layout.addWidget(self.pet_image_label)
        central_widget.setLayout(layout)

        self.bubble = SpeechBubble(self, self.config, self.theme_style)
        self.bubble.bubble_clicked.connect(self.on_bubble_clicked)
        self.bubble.reset_expression.connect(self.reset_to_default_expression)

        # Set window size from config
        self.setGeometry(100, 100, label_width, label_height)
        self.setCursor(Qt.OpenHandCursor)

        self.center_on_screen()

        logger.info(f"Pet window initialized with size {label_width}x{label_height}")

    def set_theme(self, theme_style: ThemeStyle):
        """Apply the selected UI theme to pet-owned UI."""
        self.theme_style = theme_style
        if self.bubble:
            self.bubble.apply_theme(theme_style)

    def load_and_display_expression(self, expression: str):
        """Load and display an expression image."""
        image_path = self.character_loader.get_expression_image_or_default(expression)
        
        if image_path:
            pixmap = QPixmap(str(image_path))
            if not pixmap.isNull():
                scaled_image = pixmap.scaled(
                    self.config.image_size.width,
                    self.config.image_size.height,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.pet_image_label.setPixmap(scaled_image)
                logger.info(f"Loaded expression: {expression}")
                return
        
        logger.warning(f"Failed to load expression {expression}, using placeholder")
        self.pet_image_label.setPixmap(self.draw_placeholder_pet())

    def draw_placeholder_pet(self):
        """Draw a simple placeholder pet if no image is available."""
        width = self.config.image_size.width
        height = self.config.image_size.height
        pixmap = QPixmap(width, height)
        pixmap.fill(QColor(0, 0, 0, 0))

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        # Scale drawing to match image size
        scale = width / 240.0
        
        painter.setBrush(QColor(100, 150, 200))
        painter.drawEllipse(int(75 * scale), int(60 * scale), int(90 * scale), int(105 * scale))

        painter.setBrush(QColor(255, 255, 255))
        painter.drawEllipse(int(90 * scale), int(75 * scale), int(22 * scale), int(30 * scale))
        painter.drawEllipse(int(120 * scale), int(75 * scale), int(22 * scale), int(30 * scale))

        painter.setBrush(QColor(0, 0, 0))
        painter.drawEllipse(int(97 * scale), int(83 * scale), int(15 * scale), int(15 * scale))
        painter.drawEllipse(int(128 * scale), int(83 * scale), int(15 * scale), int(15 * scale))

        painter.end()
        return pixmap

    def mousePressEvent(self, event):
        """Handle mouse press for dragging and right-click menu."""
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.pos()
            self.setCursor(Qt.ClosedHandCursor)
        elif event.button() == Qt.RightButton:
            self.context_menu_requested.emit(event.globalPos())

    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging."""
        if event.buttons() == Qt.LeftButton and self.drag_position:
            self.move(event.globalPos() - self.drag_position)
            # Notify chat panel to update position if visible
            if self.chat_panel and self.chat_panel.isVisible():
                self.chat_panel.on_pet_moved()

    def mouseReleaseEvent(self, event):
        """Handle mouse release."""
        if event.button() == Qt.LeftButton:
            self.drag_position = None
            self.setCursor(Qt.OpenHandCursor)

    def mouseDoubleClickEvent(self, event):
        """Trigger AI response and show bubble on double-click."""
        if event.button() == Qt.LeftButton:
            logger.info("Double-click detected")
            self.show_thinking_bubble()
            self.request_ai_response()
            self.drag_position = None

    def show_thinking_bubble(self):
        """Show thinking bubble while waiting for AI."""
        self.bubble_visible = True
        if self.bubble:
            self.bubble.show_bubble("我想想……", duration_ms=0)

    def request_ai_response(self):
        """Request AI response in background thread."""
        if not self.conversation_service:
            logger.warning("Conversation service not available")
            self.show_local_response()
            return
        
        def ai_request(dummy_arg=None):
            try:
                response = self.conversation_service.get_ai_response()
                self.ai_response_signal.emit(response)
            except Exception as e:
                logger.error(f"AI request failed: {e}")
                self.ai_response_signal.emit({
                    "emotion": "default",
                    "reply": "我刚刚走神了，再戳我一次吧。"
                })
        
        worker = AIWorker(ai_request, "")
        self.thread_pool.start(worker)

    def on_ai_response(self, response: dict):
        """Handle AI response."""
        try:
            emotion = response.get("emotion", "default")
            reply = response.get("reply", "……")
            
            # Validate emotion exists in config
            if emotion not in self.config.expressions:
                logger.warning(f"Invalid emotion: {emotion}, falling back to default")
                emotion = "default"
            
            # Update expression
            self.current_expression = emotion
            self.expression_index = EXPRESSION_CYCLE.index(emotion) if emotion in EXPRESSION_CYCLE else 0
            self.load_and_display_expression(emotion)
            
            # Show reply bubble (click to hide)
            self.bubble_visible = True
            if self.bubble:
                self.bubble.show_bubble(reply, duration_ms=0)
            
            logger.info(f"Updated expression to {emotion}")
        except Exception as e:
            logger.error(f"Failed to process AI response: {e}")
            self.show_local_response()

    def show_local_response(self):
        """Show local fallback response."""
        text = EXPRESSION_BUBBLE_TEXT.get(self.current_expression, "你点我干嘛！")
        logger.info(f"Showing local response: {text}")
        self.bubble_visible = True
        if self.bubble:
            self.bubble.show_bubble(text, duration_ms=0)

    def on_bubble_clicked(self):
        """Handle bubble click."""
        self.bubble_visible = False
        logger.info("Bubble was clicked and hidden")

    def reset_to_default_expression(self):
        """Reset pet expression to default."""
        logger.info("Resetting pet expression to default")
        self.current_expression = self.config.default_expression
        self.expression_index = 0
        self.load_and_display_expression(self.current_expression)

    def center_on_screen(self):
        """Center the window on the screen."""
        screen = QApplication.primaryScreen()
        if screen:
            screen_geometry = screen.geometry()
            center_x = screen_geometry.center().x() - self.width() // 2
            center_y = screen_geometry.center().y() - self.height() // 2
            self.move(center_x, center_y)
            logger.info(f"Centered pet on screen at ({center_x}, {center_y})")

    def set_visibility(self, visible):
        """Show or hide the pet window and bubble."""
        if visible:
            self.show()
            self.raise_()
        else:
            # Hide bubble when hiding pet
            self.bubble_visible = False
            if self.bubble:
                self.bubble.hide()
            # Hide chat panel when hiding pet
            if self.chat_panel and self.chat_panel.isVisible():
                self.chat_panel.hide_panel()
            self.hide()

    def set_expression(self, expression: str):
        """Set pet expression to specific emotion."""
        if expression not in self.config.expressions:
            logger.warning(f"Invalid expression: {expression}, keeping current")
            return

        self.current_expression = expression
        if expression in EXPRESSION_CYCLE:
            self.expression_index = EXPRESSION_CYCLE.index(expression)
        self.load_and_display_expression(expression)
        logger.info(f"Set expression to: {expression}")

    def show_bubble(self, message: str, auto_close: bool = True):
        """Show a bubble with message."""
        self.bubble_visible = True
        if self.bubble:
            duration_ms = 2000 if auto_close else 0
            self.bubble.show_bubble(message, duration_ms=duration_ms)
            logger.info(f"Showed bubble: {message}")
