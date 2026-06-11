from PySide6.QtWidgets import QMenu, QSystemTrayIcon
from PySide6.QtGui import QIcon, QColor, QPixmap, QPainter, QActionGroup
from PySide6.QtCore import Qt

from pet_app.utils.logger import logger
from pet_app.utils.paths import get_app_icon_path_ico, get_app_icon_path_png


class TrayMenu:
    """System tray menu for the pet app."""

    def __init__(self, app, callbacks):
        self.app = app
        self.callbacks = callbacks
        self.tray_icon = None
        self.init_tray()

    def init_tray(self):
        """Initialize the system tray icon and menu."""
        icon = self.load_app_icon()

        self.tray_icon = QSystemTrayIcon()
        self.tray_icon.setIcon(icon)

        menu = self.build_menu()
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()

        logger.info("System tray initialized")

    def refresh_menu(self):
        if self.tray_icon:
            self.tray_icon.setContextMenu(self.build_menu())

    def build_menu(self):
        """Build the context menu (reusable for tray and pet window right-click)."""
        menu = QMenu()

        show_action = menu.addAction("Show Pet")
        show_action.triggered.connect(self.callbacks["show"])

        hide_action = menu.addAction("Hide Pet")
        hide_action.triggered.connect(self.callbacks["hide"])

        menu.addSeparator()

        show_chat_action = menu.addAction("Show Chat")
        show_chat_action.triggered.connect(self.callbacks.get("show_chat", lambda: None))

        hide_chat_action = menu.addAction("Hide Chat")
        hide_chat_action.triggered.connect(self.callbacks.get("hide_chat", lambda: None))

        archive_chat_action = menu.addAction("Archive Chat Memory")
        archive_chat_action.triggered.connect(self.callbacks.get("archive_chat_memory", lambda: None))

        menu.addSeparator()

        # Voice playback
        voice_playback_menu = menu.addMenu("Voice Playback")
        is_muted = self.app.is_voice_muted() if hasattr(self.app, "is_voice_muted") else True
        playback_group = QActionGroup(voice_playback_menu)
        playback_group.setExclusive(True)

        voice_on_action = voice_playback_menu.addAction("On")
        voice_on_action.setCheckable(True)
        voice_on_action.setChecked(not is_muted)
        playback_group.addAction(voice_on_action)
        voice_on_action.triggered.connect(
            lambda _checked=False: self.callbacks.get("set_voice_muted", lambda _muted: None)(False)
        )

        voice_off_action = voice_playback_menu.addAction("Off")
        voice_off_action.setCheckable(True)
        voice_off_action.setChecked(is_muted)
        playback_group.addAction(voice_off_action)
        voice_off_action.triggered.connect(
            lambda _checked=False: self.callbacks.get("set_voice_muted", lambda _muted: None)(True)
        )

        speaker_menu = menu.addMenu("Voice Tone")
        speaker_group = QActionGroup(speaker_menu)
        speaker_group.setExclusive(True)
        current_speaker = self.callbacks.get("get_current_voice_speaker", lambda: "")()
        speaker_options = self.callbacks.get("get_voice_speakers", lambda: [])()
        if speaker_options:
            for speaker_id, speaker_name in speaker_options:
                action = speaker_menu.addAction(speaker_name)
                action.setCheckable(True)
                action.setChecked(speaker_id == current_speaker)
                action.setData(speaker_id)
                speaker_group.addAction(action)
                action.triggered.connect(
                    lambda _checked=False, sid=speaker_id: self.callbacks.get(
                        "set_voice_speaker", lambda _sid: None
                    )(sid)
                )
        else:
            no_speaker_action = speaker_menu.addAction("No voices configured")
            no_speaker_action.setEnabled(False)

        theme_menu = menu.addMenu("Theme")
        theme_group = QActionGroup(theme_menu)
        theme_group.setExclusive(True)
        current_theme = self.callbacks.get("get_current_theme", lambda: "milk")()
        theme_options = self.callbacks.get("get_theme_options", lambda: [])()
        if theme_options:
            for theme_id, theme_name in theme_options:
                action = theme_menu.addAction(theme_name)
                action.setCheckable(True)
                action.setChecked(theme_id == current_theme)
                action.setData(theme_id)
                theme_group.addAction(action)
                action.triggered.connect(
                    lambda _checked=False, tid=theme_id: self.callbacks.get(
                        "set_theme", lambda _tid: None
                    )(tid)
                )
        else:
            no_theme_action = theme_menu.addAction("No themes configured")
            no_theme_action.setEnabled(False)

        menu.addSeparator()

        # Weather
        weather_today_action = menu.addAction("Weather Today")
        weather_today_action.triggered.connect(self.callbacks.get("weather_today", lambda: None))

        weather_tomorrow_action = menu.addAction("Weather Tomorrow")
        weather_tomorrow_action.triggered.connect(self.callbacks.get("weather_tomorrow", lambda: None))

        menu.addSeparator()

        diary_feedback_action = menu.addAction("Diary Feedback")
        diary_feedback_action.triggered.connect(self.callbacks.get("diary_feedback", lambda: None))

        menu.addSeparator()

        todo_action = menu.addAction("Open Todo")
        todo_action.triggered.connect(self.callbacks.get("open_todo", lambda: None))

        menu.addSeparator()

        logs_action = menu.addAction("Open Logs")
        logs_action.triggered.connect(self.callbacks.get("open_logs", lambda: None))

        menu.addSeparator()

        quit_action = menu.addAction("Quit")
        quit_action.triggered.connect(self.callbacks["quit"])

        return menu

    def load_app_icon(self):
        """Load app icon with priority: tray.ico > tray.png > fallback blue circle."""
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
