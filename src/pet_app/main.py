"""Desktop Pet Application - Main entry point."""

import sys
from PySide6.QtWidgets import QApplication
from pet_app.app import PetApp
from pet_app.ui.loading_splash import LoadingSplash
from pet_app.utils.logger import logger


def main():
    """Main entry point for the application."""
    logger.info("Starting Desktop Pet Application")

    qt_app = QApplication(sys.argv)
    qt_app.setQuitOnLastWindowClosed(False)

    splash = LoadingSplash()
    splash.show()
    qt_app.processEvents()

    def set_loading_status(text: str):
        splash.set_status(text)
        qt_app.processEvents()

    app = PetApp(qt_app, loading_status_callback=set_loading_status)
    set_loading_status("启动完成，正在显示桌宠...")
    splash.close()
    splash.deleteLater()

    logger.info("Application running")
    sys.exit(qt_app.exec())


if __name__ == "__main__":
    main()
