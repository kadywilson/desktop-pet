from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QCoreApplication, QTimer, QThread, QRunnable, QThreadPool, QPoint

from pet_app.core.character import CharacterLoader
from pet_app.core.persona import PersonaManager
from pet_app.core.ai_client import AIClient
from pet_app.core.conversation import ConversationService
from pet_app.core.chat_config import ChatConfigManager
from pet_app.core.chat_memory import ChatMemoryService
from pet_app.core.storage import StorageManager
from pet_app.core.todo_service import TodoService
from pet_app.core.reminder_service import ReminderService
from pet_app.core.tts_player import TTSPlayer
from pet_app.core.weather_service import WeatherService
from pet_app.core.diary_feedback_service import DiaryFeedbackService
from pet_app.core.theme_config import ThemeConfigManager
from pet_app.ui.pet_window import PetWindow
from pet_app.ui.todo_window import TodoWindow
from pet_app.ui.chat_panel import ChatPanel
from pet_app.ui.tray import TrayMenu
from pet_app.utils.logger import logger
from pet_app.utils.paths import get_app_icon_path_ico, get_app_icon_path_png


class PetApp:
    """Main application controller."""

    def __init__(self, qt_app, loading_status_callback=None):
        self.qt_app = qt_app
        self.loading_status_callback = loading_status_callback
        self.character_loader = None
        self.persona_manager = None
        self.chat_config_manager = None
        self.chat_memory_service = None
        self.ai_client = None
        self.conversation_service = None
        self.storage_manager = None
        self.todo_service = None
        self.reminder_service = None
        self.reminder_timer = None
        self.tts_player = None
        self.weather_service = None
        self.diary_feedback_service = None
        self.theme_config_manager = None
        self.pet_window = None
        self.todo_window = None
        self.chat_panel = None
        self.tray_menu = None
        self.thread_pool = QThreadPool()
        self.is_visible = True
        self.chat_visible = False
        self.init_app()

    def _set_loading_status(self, text: str):
        if self.loading_status_callback:
            try:
                self.loading_status_callback(text)
            except Exception as e:
                logger.debug(f"Loading status update failed: {e}")

    def init_app(self):
        """Initialize the application."""
        logger.info("Initializing PetApp")
        self._set_loading_status("正在加载应用图标...")

        # Set application icon (for window title bar and task bar)
        app_icon = self._load_app_icon()
        self.qt_app.setWindowIcon(app_icon)

        # Initialize services
        self._set_loading_status("正在加载角色和主题...")
        self.character_loader = CharacterLoader()
        self.persona_manager = PersonaManager()
        self.chat_config_manager = ChatConfigManager()
        self.theme_config_manager = ThemeConfigManager()

        # Initialize chat memory service
        self._set_loading_status("正在加载聊天记忆...")
        chat_config = self.chat_config_manager.get_config()
        self.chat_memory_service = ChatMemoryService(
            chat_config.memory_file,
            chat_config.archive_dir,
            chat_config.max_recent_messages
        )

        self._set_loading_status("正在准备 AI 对话...")
        self.ai_client = AIClient(self.persona_manager)
        self.conversation_service = ConversationService(self.ai_client, self.chat_memory_service)

        # Initialize storage and todo service
        self._set_loading_status("正在打开待办数据库...")
        self.storage_manager = StorageManager()
        self.todo_service = TodoService(self.storage_manager)

        # Initialize reminder service
        self._set_loading_status("正在准备提醒服务...")
        self.reminder_service = ReminderService(self.todo_service, self.ai_client)
        self.reminder_service.set_on_reminder_callback(self._on_reminder)

        # Initialize TTS player
        self._set_loading_status("正在准备语音播放...")
        self.tts_player = TTSPlayer()

        # Initialize weather service
        self._set_loading_status("正在准备天气服务...")
        try:
            self.weather_service = WeatherService()
            logger.info("Weather service initialized")
        except Exception as e:
            logger.warning(f"Weather service init failed: {e}")
            self.weather_service = None

        # Wire weather service to AI client for context injection
        if self.weather_service:
            self.ai_client.set_weather_service(self.weather_service)

        # Initialize diary feedback service
        self._set_loading_status("正在准备日记联动...")
        self.diary_feedback_service = DiaryFeedbackService()

        # Initialize UI
        self._set_loading_status("正在打开桌宠窗口...")
        current_theme = self.theme_config_manager.get_current_theme()
        self.pet_window = PetWindow(
            self.character_loader,
            self.conversation_service,
            theme_style=current_theme,
        )
        self.pet_window.show()

        # Connect poke AI response to TTS
        self.pet_window.ai_response_signal.connect(self._on_poke_response_for_tts)

        # Initialize chat panel
        self.chat_panel = ChatPanel(self.pet_window, theme_style=current_theme)
        self.chat_panel.message_sent.connect(self._on_chat_message_sent)
        # Cross-reference for pet window
        self.pet_window.chat_panel = self.chat_panel

        # Connect pet window context menu signal
        self.pet_window.context_menu_requested.connect(self._on_pet_context_menu_requested)

        # Initialize tray
        self._set_loading_status("正在创建托盘菜单...")
        callbacks = {
            "show": self.show_pet,
            "hide": self.hide_pet,
            "show_chat": self.show_chat,
            "hide_chat": self.hide_chat,
            "archive_chat_memory": self.archive_chat_memory,
            "toggle_voice": self.toggle_voice,
            "set_voice_muted": self.set_voice_muted,
            "get_voice_speakers": self.get_voice_speakers,
            "get_current_voice_speaker": self.get_current_voice_speaker,
            "set_voice_speaker": self.set_voice_speaker,
            "get_theme_options": self.get_theme_options,
            "get_current_theme": self.get_current_theme,
            "set_theme": self.set_theme,
            "weather_today": self.weather_today,
            "weather_tomorrow": self.weather_tomorrow,
            "diary_feedback": self.diary_feedback,
            "open_todo": self.open_todo,
            "open_logs": self.open_logs,
            "quit": self.quit_app,
        }
        self.tray_menu = TrayMenu(self, callbacks)

        # Start reminder timer (scan every 60 seconds)
        self._set_loading_status("正在启动提醒计时器...")
        self.reminder_timer = QTimer()
        self.reminder_timer.timeout.connect(self._check_reminders)
        self.reminder_timer.start(60000)  # 60 seconds
        logger.info("Reminder timer started (60s interval)")

        logger.info("PetApp initialized successfully")
        
        if self.ai_client.is_available():
            logger.info("AI client available, ready to accept AI requests")
            persona_config = self.persona_manager.get_config()
            logger.info(f"Persona loaded: {persona_config.name}")
        else:
            logger.warning("AI client not available, using local fallback replies")

    def _load_app_icon(self):
        """Load app icon with priority: tray.ico > tray.png > fallback blue circle."""
        from PySide6.QtGui import QIcon, QColor, QPixmap, QPainter

        # Try loading tray.ico first
        ico_path = get_app_icon_path_ico()
        if ico_path:
            icon = QIcon(str(ico_path))
            if not icon.isNull():
                logger.info(f"Loaded app icon from: {ico_path}")
                return icon
            logger.warning(f"Failed to load icon from {ico_path}, icon is null")

        # Try loading tray.png second
        png_path = get_app_icon_path_png()
        if png_path:
            icon = QIcon(str(png_path))
            if not icon.isNull():
                logger.info(f"Loaded app icon from: {png_path}")
                return icon
            logger.warning(f"Failed to load icon from {png_path}, icon is null")

        # Fallback: create blue circle placeholder
        logger.warning("No custom icon found, using fallback blue circle")
        pixmap = QPixmap(32, 32)
        pixmap.fill(QColor(0, 0, 0, 0))

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(100, 150, 200))
        painter.drawEllipse(4, 4, 24, 24)
        painter.end()

        return QIcon(pixmap)

    def show_pet(self):
        """Show the pet window."""
        logger.info("Showing pet")
        self.is_visible = True
        self.pet_window.set_visibility(True)

    def hide_pet(self):
        """Hide the pet window and bubble."""
        logger.info("Hiding pet")
        self.is_visible = False
        self.pet_window.set_visibility(False)
        # Also hide chat panel when hiding pet
        if self.chat_panel and self.chat_panel.isVisible():
            self.chat_panel.hide_panel()
            self.chat_visible = False

    def show_chat(self):
        """Show the chat panel."""
        logger.info("Showing chat panel")
        self.chat_visible = True
        if self.chat_panel:
            self.chat_panel.show_panel()

    def hide_chat(self):
        """Hide the chat panel."""
        logger.info("Hiding chat panel")
        self.chat_visible = False
        if self.chat_panel:
            self.chat_panel.hide_panel()

    def toggle_voice(self):
        """Toggle TTS mute state."""
        if self.tts_player:
            muted = self.tts_player.toggle_mute()
            state = "off" if muted else "on"
            logger.info(f"Voice toggled: {state}")
            self._refresh_tray_menu()

    def set_voice_muted(self, muted: bool):
        """Set TTS mute state from the voice playback menu."""
        if self.tts_player:
            self.tts_player.set_muted(muted)
            state = "off" if muted else "on"
            logger.info(f"Voice playback set from menu: {state}")
            self._refresh_tray_menu()

    def is_voice_muted(self) -> bool:
        """Return current mute state for menu display."""
        if self.tts_player:
            return self.tts_player.muted
        return True

    def get_voice_speakers(self) -> list[tuple[str, str]]:
        """Return configured TTS speaker options for the menu."""
        if self.tts_player:
            return self.tts_player.get_speaker_options()
        return []

    def get_current_voice_speaker(self) -> str:
        """Return the currently selected TTS speaker id."""
        if self.tts_player:
            return self.tts_player.current_speaker()
        return ""

    def set_voice_speaker(self, speaker_id: str):
        """Switch TTS speaker at runtime and persist the choice."""
        if not self.tts_player:
            return

        if self.tts_player.set_speaker(speaker_id, persist=True):
            logger.info(f"Voice speaker selected from menu: {speaker_id}")
            self._refresh_tray_menu()

    def get_theme_options(self) -> list[tuple[str, str]]:
        """Return available UI themes for the menu."""
        if self.theme_config_manager:
            return self.theme_config_manager.get_theme_options()
        return []

    def get_current_theme(self) -> str:
        """Return current UI theme id for menu display."""
        if self.theme_config_manager:
            return self.theme_config_manager.get_current_theme_id()
        return "milk"

    def set_theme(self, theme_id: str):
        """Switch bubble and chat input theme at runtime."""
        if not self.theme_config_manager:
            return

        if not self.theme_config_manager.set_theme(theme_id, persist=True):
            return

        theme = self.theme_config_manager.get_current_theme()
        if self.pet_window:
            self.pet_window.set_theme(theme)
        if self.chat_panel:
            self.chat_panel.set_theme(theme)

        logger.info(f"UI theme selected from menu: {theme_id}")
        self._refresh_tray_menu()

    def _refresh_tray_menu(self):
        if self.tray_menu and hasattr(self.tray_menu, "refresh_menu"):
            self.tray_menu.refresh_menu()

    def weather_today(self):
        """Show today's weather in bubble."""
        self._request_weather("today")

    def weather_tomorrow(self):
        """Show tomorrow's weather in bubble."""
        self._request_weather("tomorrow")

    def diary_feedback(self):
        """Import the latest saved diary context into active chat memory."""
        logger.info("[DiaryFeedback] User requested latest diary feedback")
        if not self.diary_feedback_service:
            self.pet_window.show_bubble("日记反馈功能暂时不可用。", auto_close=False)
            return

        context = self.diary_feedback_service.load_latest()
        if context is None:
            self.pet_window.show_bubble("还没有发给我的今日小纸条哦。", auto_close=False)
            return

        if not self.chat_memory_service:
            self.pet_window.show_bubble("聊天记忆暂时不可用。", auto_close=False)
            return

        reply = "我读到了。哼……之后你想聊的话，我会记得的。"
        ok_context = self.chat_memory_service.append_diary_context(context.pet_context)
        ok_reply = self.chat_memory_service.append_diary_context_reply(reply, "default")

        if not (ok_context and ok_reply):
            self.pet_window.show_bubble("小纸条读到了，但写进记忆时出错了。", auto_close=False)
            return

        self.pet_window.set_expression("default")
        self.pet_window.show_bubble("我读到今天的小纸条了。之后可以和我聊这个。", auto_close=False)

    def _request_weather(self, day: str):
        """Request weather and show in bubble (non-blocking)."""
        logger.info(f"[Weather] User requested weather: {day}")

        thinking = "我看看天气……" if day == "today" else "我看看明天天气……"
        self.pet_window.show_bubble(thinking, auto_close=False)

        def weather_worker():
            try:
                if not self.weather_service:
                    text = "天气功能暂时不可用。"
                else:
                    text = self.weather_service.get_weather_text(day)
                response = {"emotion": "default", "reply": text, "_source": "weather"}
                self.pet_window.ai_response_signal.emit(response)
            except Exception as e:
                logger.error(f"[Weather] Worker error: {e}")
                fallback = {"emotion": "default", "reply": "天气暂时查不到啦，可能是网络有点闹脾气。", "_source": "weather"}
                self.pet_window.ai_response_signal.emit(fallback)

        class WeatherWorker(QRunnable):
            def __init__(self, callback):
                super().__init__()
                self.callback = callback

            def run(self):
                self.callback()

        worker = WeatherWorker(weather_worker)
        self.thread_pool.start(worker)

    def _on_poke_response_for_tts(self, response: dict):
        """Trigger TTS for poke/chat/weather AI response."""
        reply = response.get("reply", "")
        emotion = response.get("emotion", "default")
        source = response.get("_source", "poke")

        if source == "weather":
            if self.weather_service and not self.weather_service._config.speak_if_voice_enabled:
                return

        if reply and self.tts_player:
            self.tts_player.speak(reply, emotion, source=source)

    def archive_chat_memory(self):
        """Archive current chat memory and start new memory segment."""
        logger.info("[Archive] User initiated chat memory archive")

        # Show confirmation dialog
        msg_box = QMessageBox()
        msg_box.setWindowTitle("Archive Chat Memory")
        msg_box.setText("Archive current chat memory?")
        msg_box.setInformativeText(
            "The current chat memory will be saved as an archive file.\n"
            "A new active memory will start after this.\n"
            "Archived memory will not be used in future replies unless archive search is added later."
        )
        msg_box.setStandardButtons(QMessageBox.Cancel | QMessageBox.Ok)
        msg_box.setDefaultButton(QMessageBox.Cancel)
        msg_box.button(QMessageBox.Ok).setText("Archive")
        msg_box.button(QMessageBox.Cancel).setText("Cancel")

        result = msg_box.exec()

        if result != QMessageBox.Ok:
            logger.info("[Archive] User cancelled archive operation")
            return

        # Proceed with archiving
        try:
            logger.info("[Archive] Archiving current chat memory...")
            archive_path = self.chat_memory_service.archive_current_memory()

            if archive_path is None:
                logger.info("[Archive] No chat memory to archive (empty or non-existent)")
                info_box = QMessageBox()
                info_box.setWindowTitle("Archive Chat Memory")
                info_box.setText("No chat memory to archive.")
                info_box.setInformativeText("The current chat memory is empty.")
                info_box.setStandardButtons(QMessageBox.Ok)
                info_box.exec()
            else:
                logger.info(f"[Archive] Successfully archived to: {archive_path}")
                success_box = QMessageBox()
                success_box.setWindowTitle("Archive Chat Memory")
                success_box.setText("Chat memory archived successfully!")
                success_box.setInformativeText(
                    "Your current chat memory has been saved.\n"
                    "A new chat memory has started."
                )
                success_box.setStandardButtons(QMessageBox.Ok)
                success_box.exec()

        except Exception as e:
            logger.error(f"[Archive] Failed to archive chat memory: {e}")
            error_box = QMessageBox()
            error_box.setWindowTitle("Archive Failed")
            error_box.setText("Failed to archive chat memory.")
            error_box.setInformativeText(
                "Your current chat memory has been preserved.\n"
                "Please check the logs for details."
            )
            error_box.setStandardButtons(QMessageBox.Ok)
            error_box.setIcon(QMessageBox.Warning)
            error_box.exec()

    def _on_pet_context_menu_requested(self, position: "QPoint"):
        """Handle right-click context menu on pet window."""
        logger.info(f"[Context Menu] Right-click detected at position {position.x()}, {position.y()}")
        if self.tray_menu:
            menu = self.tray_menu.build_menu()
            menu.exec(position)
            logger.info("[Context Menu] Menu displayed")

    def _on_chat_message_sent(self, message: str):
        """Handle message sent from chat panel."""
        if not message or not message.strip():
            logger.debug("Chat message is empty, skipping")
            return

        logger.info(f"[Chat] Message received: {message[:50]}...")

        # Truncate if needed
        chat_config = self.chat_config_manager.get_config()
        max_chars = chat_config.max_user_input_chars if chat_config else 300
        if len(message) > max_chars:
            message = message[:max_chars]
            logger.info(f"[Chat] Message truncated to {max_chars} characters")

        # Write user message to memory
        if self.chat_memory_service:
            self.chat_memory_service.append_user_message(message)

        # Show thinking bubble
        thinking_text = chat_config.thinking_text if chat_config else "我想想……"
        self.pet_window.show_bubble(thinking_text, auto_close=False)

        # Request AI response in background
        def chat_ai_request():
            try:
                response = self.conversation_service.get_chat_response(message, chat_config)
                if response:
                    # Write pet reply to memory
                    emotion = response.get("emotion", "default")
                    reply = response.get("reply", "")
                    if self.chat_memory_service:
                        self.chat_memory_service.append_pet_reply(reply, emotion)

                    response["_source"] = "chat"
                    self.pet_window.ai_response_signal.emit(response)
            except Exception as e:
                logger.error(f"[Chat] AI request failed: {e}")
                fallback_response = {
                    "emotion": "default",
                    "reply": "我刚刚走神了，你再说一次嘛。",
                    "_source": "chat",
                }
                # Also write fallback to memory
                if self.chat_memory_service:
                    self.chat_memory_service.append_pet_reply(
                        fallback_response["reply"],
                        fallback_response["emotion"]
                    )
                self.pet_window.ai_response_signal.emit(fallback_response)

        # Create and start worker thread
        class ChatAIWorker(QRunnable):
            def __init__(self, callback):
                super().__init__()
                self.callback = callback

            def run(self):
                self.callback()

        worker = ChatAIWorker(chat_ai_request)
        self.thread_pool.start(worker)

    def open_todo(self):
        """Open todo window."""
        logger.info("Opening todo window")

        if self.todo_window is None or not self.todo_window.isVisible():
            self.todo_window = TodoWindow(self.todo_service)
            self.todo_window.destroyed.connect(lambda: setattr(self, 'todo_window', None))
            self.todo_window.show()
        else:
            # Bring to front if already open
            self.todo_window.raise_()
            self.todo_window.activateWindow()

    def _check_reminders(self):
        """Check for pending reminders (called by QTimer)."""
        if not self.is_visible:
            logger.debug("[Timer] Pet is hidden, skip reminder check")
            return

        logger.debug("[Timer] Running reminder scan (60s interval)")
        self.reminder_service.scan_reminders()

    def _on_reminder(self, reminder_data: dict):
        """Handle reminder callback from ReminderService."""
        try:
            logger.info(f"Displaying reminder: {reminder_data['title']}")
            emotion = reminder_data.get("emotion", "default")
            message = reminder_data.get("message", "有一个待办快到期了")

            # Switch pet expression if available
            self.pet_window.set_expression(emotion)

            # Show reminder in bubble
            self.pet_window.show_bubble(message, auto_close=False)

            # Trigger TTS for reminder
            if self.tts_player:
                self.tts_player.speak(message, emotion, source="reminder")

        except Exception as e:
            logger.error(f"Error displaying reminder: {e}")

    def open_logs(self):
        """Open logs file or logs directory."""
        try:
            from pet_app.utils.paths import get_logs_dir
            import os
            import platform

            logs_dir = get_logs_dir()
            log_file = logs_dir / "pet_app.log"

            # Try to open log file if it exists
            if log_file.exists():
                logger.info(f"Opening log file: {log_file}")
                if platform.system() == "Windows":
                    os.startfile(str(log_file))
                else:
                    os.system(f"open '{log_file}'")
            else:
                # Open logs directory if file doesn't exist
                logger.info(f"Opening logs directory: {logs_dir}")
                if platform.system() == "Windows":
                    os.startfile(str(logs_dir))
                else:
                    os.system(f"open '{logs_dir}'")

        except Exception as e:
            logger.error(f"Failed to open logs: {e}")

    def quit_app(self):
        """Quit the application."""
        logger.info("Quitting application")

        # Stop TTS playback
        if self.tts_player:
            self.tts_player.cleanup()

        # Stop reminder timer
        if self.reminder_timer:
            self.reminder_timer.stop()

        # Stop chat panel position timer
        if self.chat_panel:
            if hasattr(self.chat_panel, 'position_update_timer'):
                self.chat_panel.position_update_timer.stop()

        # Wait for thread pool to finish
        if self.thread_pool:
            self.thread_pool.waitForDone()

        # Close todo window if open
        if self.todo_window:
            self.todo_window.close()

        # Close storage
        if self.storage_manager:
            self.storage_manager.close()

        QCoreApplication.quit()
