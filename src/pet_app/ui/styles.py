"""UI Styles for Todo Window - Limited to TodoWindow scope."""

# Color palette
COLORS = {
    "bg_main": "#FAF7F0",
    "bg_card": "#FFFFFF",
    "text_primary": "#2F2F2F",
    "text_secondary": "#8A8178",
    "border": "#DED6C8",
    "button_primary": "#8FB996",
    "button_edit": "#A7BED3",
    "button_delete": "#E07A7A",
    "row_hover": "#F6F1E8",
    "row_done": "#EEEEEE",
    "row_overdue": "#FFECEC",
}

# TodoWindow stylesheet - scoped to TodoWindow and children only
TODO_WINDOW_STYLESHEET = f"""
QMainWindow#TodoWindow {{
    background-color: {COLORS["bg_main"]};
}}

QMainWindow#TodoWindow QWidget {{
    background-color: {COLORS["bg_main"]};
    color: {COLORS["text_primary"]};
}}

QMainWindow#TodoWindow QLabel {{
    color: {COLORS["text_primary"]};
    background-color: transparent;
    border: none;
}}

QMainWindow#TodoWindow QFrame#inputCard {{
    background-color: {COLORS["bg_card"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 8px;
}}

QMainWindow#TodoWindow QFrame#listCard {{
    background-color: {COLORS["bg_card"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 8px;
}}

QMainWindow#TodoWindow QLineEdit,
QMainWindow#TodoWindow QTextEdit {{
    background-color: white;
    color: {COLORS["text_primary"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 6px;
    padding: 6px 8px;
    font-size: 12px;
}}

QMainWindow#TodoWindow QLineEdit:focus,
QMainWindow#TodoWindow QTextEdit:focus {{
    border: 2px solid {COLORS["button_primary"]};
    background-color: white;
}}

QMainWindow#TodoWindow QLineEdit::placeholder {{
    color: #CCCCCC;
}}

QMainWindow#TodoWindow QDateTimeEdit {{
    background-color: white;
    color: {COLORS["text_primary"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 6px;
    padding: 6px 8px;
    font-size: 12px;
}}

QMainWindow#TodoWindow QDateTimeEdit:focus {{
    border: 2px solid {COLORS["button_primary"]};
}}

QMainWindow#TodoWindow QDateTimeEdit::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 36px;
    border-left: 1px solid {COLORS["border"]};
    border-top-right-radius: 6px;
    border-bottom-right-radius: 6px;
    background-color: #F5F0E8;
}}

QMainWindow#TodoWindow QDateTimeEdit::drop-down:hover {{
    background-color: #E8E0D4;
}}

QMainWindow#TodoWindow QDateTimeEdit::down-arrow {{
    image: url(:/qt/img/down_arrow.png);
    width: 12px;
    height: 12px;
}}

QMainWindow#TodoWindow QPushButton {{
    border-radius: 6px;
    padding: 6px 12px;
    font-weight: 500;
    font-size: 12px;
    border: none;
    min-width: 60px;
    min-height: 24px;
}}

QMainWindow#TodoWindow QPushButton:hover {{
    opacity: 0.88;
}}

QMainWindow#TodoWindow QPushButton:pressed {{
    opacity: 0.76;
}}

QMainWindow#TodoWindow QPushButton#addButton {{
    background-color: {COLORS["button_primary"]};
    color: white;
    min-width: 80px;
}}

QMainWindow#TodoWindow QPushButton#editButton {{
    background-color: {COLORS["button_edit"]};
    color: white;
    min-width: 72px;
    min-height: 28px;
}}

QMainWindow#TodoWindow QPushButton#editButton:hover {{
    background-color: #8FAFC8;
}}

QMainWindow#TodoWindow QPushButton#deleteButton {{
    background-color: {COLORS["button_delete"]};
    color: white;
    min-width: 72px;
    min-height: 28px;
}}

QMainWindow#TodoWindow QPushButton#deleteButton:hover {{
    background-color: #D86666;
}}

QMainWindow#TodoWindow QTableWidget {{
    background-color: white;
    alternate-background-color: white;
    gridline-color: #EEEEEE;
    border: none;
}}

QMainWindow#TodoWindow QTableWidget::item {{
    padding: 4px;
    border: none;
    background-color: white;
}}

QMainWindow#TodoWindow QTableWidget::item:selected {{
    background-color: {COLORS["row_hover"]};
}}

QMainWindow#TodoWindow QHeaderView::section {{
    background-color: #F9F7F4;
    color: {COLORS["text_primary"]};
    padding: 8px;
    border: none;
    border-bottom: 1px solid {COLORS["border"]};
    font-weight: 600;
    font-size: 11px;
}}

QMainWindow#TodoWindow QCheckBox {{
    spacing: 6px;
    background-color: transparent;
    border: none;
}}

QMainWindow#TodoWindow QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    background-color: white;
    border: 2px solid {COLORS["border"]};
    border-radius: 3px;
}}

QMainWindow#TodoWindow QCheckBox::indicator:checked {{
    background-color: {COLORS["button_primary"]};
    border: 2px solid {COLORS["button_primary"]};
}}

QMainWindow#TodoWindow QMessageBox {{
    background-color: {COLORS["bg_main"]};
}}

QMainWindow#TodoWindow QMessageBox QLabel {{
    color: {COLORS["text_primary"]};
}}

QMainWindow#TodoWindow QScrollBar:vertical {{
    width: 8px;
    background-color: {COLORS["bg_main"]};
}}

QMainWindow#TodoWindow QScrollBar::handle:vertical {{
    background-color: {COLORS["border"]};
    border-radius: 4px;
    min-height: 40px;
}}

QMainWindow#TodoWindow QScrollBar::handle:vertical:hover {{
    background-color: #CCCCCC;
}}
"""
