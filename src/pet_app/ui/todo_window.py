from datetime import datetime
from functools import partial
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QPushButton, QTableWidget, QTableWidgetItem, QMessageBox,
    QDateTimeEdit, QHeaderView, QCheckBox, QFrame, QGridLayout
)
from PySide6.QtCore import Qt, QDateTime, QDate
from PySide6.QtGui import QFont, QColor

from pet_app.core.todo_service import TodoService
from pet_app.ui.styles import TODO_WINDOW_STYLESHEET, COLORS
from pet_app.utils.logger import logger


class TodoWindow(QMainWindow):
    """Todo management window."""

    def __init__(self, todo_service: TodoService):
        super().__init__()
        self.setObjectName("TodoWindow")
        self.todo_service = todo_service
        self.current_edit_id = None
        self.init_ui()
        self.load_todos()
        self.setStyleSheet(TODO_WINDOW_STYLESHEET)

    def init_ui(self):
        """Initialize UI."""
        self.setWindowTitle("待办事项")
        self.setGeometry(400, 200, 900, 640)
        self.setMinimumSize(750, 550)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        # ===== Header Section =====
        header_layout = QVBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(4)

        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setWeight(QFont.Bold)
        title_label = QLabel("待办事项")
        title_label.setFont(title_font)

        subtitle_label = QLabel("记录任务和截止时间，之后桌宠会提醒你")
        subtitle_font = QFont()
        subtitle_font.setPointSize(10)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setStyleSheet("color: #8A8178;")

        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        main_layout.addLayout(header_layout)

        # ===== Input Card Section =====
        input_card = QFrame()
        input_card.setObjectName("inputCard")
        input_card.setLineWidth(0)
        input_card.setFrameShape(QFrame.StyledPanel)
        input_card.setFrameShadow(QFrame.Plain)

        input_layout = QGridLayout()
        input_layout.setContentsMargins(16, 16, 16, 12)
        input_layout.setSpacing(12)

        # Title row
        title_label_field = QLabel("标题")
        title_label_field.setObjectName("formLabel")
        title_label_field.setFixedWidth(72)
        title_label_font = QFont()
        title_label_font.setPointSize(11)
        title_label_font.setWeight(QFont.Normal)
        title_label_field.setFont(title_label_font)
        title_label_field.setStyleSheet("color: #2F2F2F; background: transparent; border: none; padding: 0px;")

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("输入待办标题")
        self.title_input.setMinimumHeight(32)

        input_layout.addWidget(title_label_field, 0, 0, 1, 1)
        input_layout.addWidget(self.title_input, 0, 1, 1, 2)

        # Description row
        desc_label_field = QLabel("描述")
        desc_label_field.setObjectName("formLabel")
        desc_label_field.setFixedWidth(72)
        desc_label_font = QFont()
        desc_label_font.setPointSize(11)
        desc_label_font.setWeight(QFont.Normal)
        desc_label_field.setFont(desc_label_font)
        desc_label_field.setAlignment(Qt.AlignTop)
        desc_label_field.setStyleSheet("color: #2F2F2F; background: transparent; border: none; padding: 0px;")

        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("输入待办描述（可选）")
        self.desc_input.setMinimumHeight(88)
        self.desc_input.setMaximumHeight(110)

        input_layout.addWidget(desc_label_field, 1, 0, 1, 1, Qt.AlignTop)
        input_layout.addWidget(self.desc_input, 1, 1, 1, 2)

        # DDL row
        ddl_label_field = QLabel("截止时间")
        ddl_label_field.setObjectName("formLabel")
        ddl_label_field.setFixedWidth(72)
        ddl_label_font = QFont()
        ddl_label_font.setPointSize(11)
        ddl_label_font.setWeight(QFont.Normal)
        ddl_label_field.setFont(ddl_label_font)
        ddl_label_field.setStyleSheet("color: #2F2F2F; background: transparent; border: none; padding: 0px;")

        self.ddl_input = QDateTimeEdit()
        self.ddl_input.setDateTime(QDateTime.currentDateTime())
        self.ddl_input.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.ddl_input.setCalendarPopup(True)
        self.ddl_input.setMinimumHeight(32)

        add_button = QPushButton("新增")
        add_button.setObjectName("addButton")
        add_button.setFixedWidth(96)
        add_button.setMinimumHeight(32)
        add_button.clicked.connect(self.add_todo)

        input_layout.addWidget(ddl_label_field, 2, 0, 1, 1)
        input_layout.addWidget(self.ddl_input, 2, 1, 1, 1)
        input_layout.addWidget(add_button, 2, 2, 1, 1)

        input_card.setLayout(input_layout)
        main_layout.addWidget(input_card)

        # ===== List Card Section =====
        list_card = QFrame()
        list_card.setObjectName("listCard")
        list_card.setLineWidth(0)
        list_card.setFrameShape(QFrame.StyledPanel)
        list_card.setFrameShadow(QFrame.Plain)

        list_layout = QVBoxLayout()
        list_layout.setContentsMargins(16, 16, 16, 16)
        list_layout.setSpacing(12)

        list_title_font = QFont()
        list_title_font.setPointSize(12)
        list_title_font.setWeight(QFont.Bold)
        list_title = QLabel("待办列表")
        list_title.setFont(list_title_font)
        list_layout.addWidget(list_title)

        # Todo table
        self.todo_table = QTableWidget()
        self.todo_table.setColumnCount(6)
        self.todo_table.setHorizontalHeaderLabels(["✓", "标题", "描述", "截止时间", "编辑", "删除"])

        # Setup table
        self.todo_table.verticalHeader().setVisible(False)
        self.todo_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.todo_table.setSelectionMode(QTableWidget.NoSelection)
        self.todo_table.setShowGrid(False)
        self.todo_table.setAlternatingRowColors(False)

        header = self.todo_table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        header.setSectionResizeMode(5, QHeaderView.Fixed)

        self.todo_table.setColumnWidth(0, 64)
        self.todo_table.setColumnWidth(1, 220)
        self.todo_table.setColumnWidth(3, 200)
        self.todo_table.setColumnWidth(4, 100)
        self.todo_table.setColumnWidth(5, 100)

        self.todo_table.setMinimumHeight(280)

        list_layout.addWidget(self.todo_table)

        # Empty hint
        self.empty_hint = QLabel("还没有待办，先添加一个吧。")
        self.empty_hint.setAlignment(Qt.AlignCenter)
        empty_hint_font = QFont()
        empty_hint_font.setPointSize(11)
        self.empty_hint.setFont(empty_hint_font)
        self.empty_hint.setStyleSheet("color: #CCCCCC; padding: 60px;")
        self.empty_hint.setVisible(False)
        list_layout.addWidget(self.empty_hint)

        list_card.setLayout(list_layout)
        main_layout.addWidget(list_card)

        main_layout.addStretch()
        central_widget.setLayout(main_layout)

        logger.info("TodoWindow UI initialized")

    def add_todo(self):
        """Add a new todo item."""
        title = self.title_input.text().strip()
        description = self.desc_input.toPlainText().strip()
        ddl = self.ddl_input.dateTime().toString("yyyy-MM-dd HH:mm:ss")

        if not title:
            QMessageBox.warning(self, "温和提示", "标题不能为空哦")
            return

        try:
            if self.current_edit_id:
                self.todo_service.update_todo(self.current_edit_id, title, description or None, ddl)
                logger.info(f"Todo updated: {title}")
                self.current_edit_id = None
            else:
                self.todo_service.create_todo(title, description or None, ddl)
                logger.info(f"Todo added: {title}")

            self.title_input.clear()
            self.desc_input.clear()
            self.ddl_input.setDateTime(QDateTime.currentDateTime())
            self.load_todos()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"操作失败: {e}")
            logger.error(f"Failed to add/update todo: {e}")

    def get_row_color(self, todo) -> tuple:
        """Determine row color based on todo state."""
        now = QDateTime.currentDateTime()
        ddl_datetime = QDateTime.fromString(todo.ddl, "yyyy-MM-dd HH:mm:ss") if todo.ddl else None

        if todo.is_done:
            # Completed: light gray
            return (COLORS["row_done"], "#999999")

        elif ddl_datetime and ddl_datetime < now:
            # Overdue: light red
            return (COLORS["row_overdue"], "#2F2F2F")

        else:
            # Normal: white
            return ("#FFFFFF", COLORS["text_primary"])

    def load_todos(self):
        """Load and display all todos."""
        try:
            todos = self.todo_service.get_all_todos()
            self.todo_table.setRowCount(0)

            if not todos:
                self.todo_table.setVisible(False)
                self.empty_hint.setVisible(True)
                return

            self.todo_table.setVisible(True)
            self.empty_hint.setVisible(False)

            for row, todo in enumerate(todos):
                self.todo_table.insertRow(row)
                self.todo_table.setRowHeight(row, 56)

                bg_color, text_color = self.get_row_color(todo)

                # Checkbox for completion
                checkbox = QCheckBox()
                checkbox.setChecked(bool(todo.is_done))
                checkbox.stateChanged.connect(partial(self.toggle_done, todo.id))
                self.todo_table.setCellWidget(row, 0, checkbox)

                # Title with strikethrough if done
                title_item = QTableWidgetItem(todo.title)
                title_item.setForeground(QColor(text_color))
                if todo.is_done:
                    font = title_item.font()
                    font.setStrikeOut(True)
                    title_item.setFont(font)
                title_item.setBackground(QColor(bg_color))
                self.todo_table.setItem(row, 1, title_item)

                # Description
                desc_item = QTableWidgetItem(todo.description or "")
                desc_item.setForeground(QColor(text_color))
                desc_item.setBackground(QColor(bg_color))
                self.todo_table.setItem(row, 2, desc_item)

                # DDL
                ddl_item = QTableWidgetItem(todo.ddl or "")
                ddl_item.setForeground(QColor(text_color))
                ddl_item.setBackground(QColor(bg_color))
                self.todo_table.setItem(row, 3, ddl_item)

                # Edit button
                edit_btn = QPushButton("编辑")
                edit_btn.setObjectName("editButton")
                edit_btn.setCursor(Qt.PointingHandCursor)
                edit_btn.clicked.connect(partial(self.edit_todo, todo.id))
                self.todo_table.setCellWidget(row, 4, edit_btn)

                # Delete button
                del_btn = QPushButton("删除")
                del_btn.setObjectName("deleteButton")
                del_btn.setCursor(Qt.PointingHandCursor)
                del_btn.clicked.connect(partial(self.delete_todo, todo.id))
                self.todo_table.setCellWidget(row, 5, del_btn)

            logger.info(f"Loaded {len(todos)} todos")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载待办失败: {e}")
            logger.error(f"Failed to load todos: {e}")

    def toggle_done(self, todo_id: int):
        """Toggle todo completion status."""
        try:
            self.todo_service.toggle_done(todo_id)
            self.load_todos()
            logger.info(f"Todo {todo_id} toggled")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"更新待办失败: {e}")
            logger.error(f"Failed to toggle todo: {e}")

    def edit_todo(self, todo_id: int):
        """Edit a todo item."""
        try:
            todo = self.todo_service.get_todo(todo_id)
            if not todo:
                return

            self.title_input.setText(todo.title)
            self.desc_input.setText(todo.description or "")
            if todo.ddl:
                dt = QDateTime.fromString(todo.ddl, "yyyy-MM-dd HH:mm:ss")
                self.ddl_input.setDateTime(dt)

            self.current_edit_id = todo_id
            self.title_input.setFocus()
            logger.info(f"Editing todo {todo_id}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"编辑待办失败: {e}")
            logger.error(f"Failed to edit todo: {e}")

    def delete_todo(self, todo_id: int):
        """Delete a todo item."""
        reply = QMessageBox.question(self, "确认", "确定要删除这个待办吗？")
        if reply != QMessageBox.Yes:
            return

        try:
            self.todo_service.delete_todo(todo_id)
            self.load_todos()
            logger.info(f"Todo {todo_id} deleted")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"删除待办失败: {e}")
            logger.error(f"Failed to delete todo: {e}")

    def closeEvent(self, event):
        """Handle window close event."""
        logger.info("Closing TodoWindow")
        event.accept()
        self.deleteLater()
