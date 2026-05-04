from pathlib import Path

from PySide6.QtGui import QFont


def apply_theme(app):
    icons_dir = (Path(__file__).resolve().parent / "icons").as_posix()
    checkbox_unchecked = f"{icons_dir}/checkbox_unchecked.svg"
    checkbox_checked = f"{icons_dir}/checkbox_checked.svg"
    checkbox_unchecked_disabled = f"{icons_dir}/checkbox_unchecked_disabled.svg"
    checkbox_checked_disabled = f"{icons_dir}/checkbox_checked_disabled.svg"
    arrow_up = f"{icons_dir}/arrow_up.svg"
    arrow_down = f"{icons_dir}/arrow_down.svg"

    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))
    stylesheet = """
        QWidget {
            background-color: #0d1117;
            color: #c9d1d9;
            font-family: "Segoe UI", Arial, sans-serif;
            font-size: 10pt;
        }

        QMainWindow,
        QDialog {
            background-color: #0d1117;
        }

        QLabel {
            color: #c9d1d9;
        }

        QLabel#pageTitle {
            color: #f0f6fc;
            font-size: 18pt;
            font-weight: 700;
        }

        QLabel#pageSubtitle {
            color: #8b949e;
            font-size: 10pt;
        }

        QGroupBox {
            background-color: #161b22;
            border: 1px solid #30363d;
            border-radius: 6px;
            margin-top: 12px;
            padding: 14px;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 6px;
            color: #8b949e;
            font-weight: 600;
            background-color: #0d1117;
        }

        QPushButton,
        QToolButton {
            background-color: #21262d;
            border: 1px solid #30363d;
            border-radius: 6px;
            color: #f0f6fc;
            font-weight: 600;
            min-height: 30px;
            padding: 7px 14px;
        }

        QPushButton:hover,
        QToolButton:hover {
            background-color: #30363d;
            border-color: #484f58;
        }

        QPushButton:pressed,
        QToolButton:pressed {
            background-color: #1b1f24;
            border-color: #30363d;
        }

        QPushButton:checked,
        QToolButton:checked {
            background-color: #1f6feb;
            border-color: #388bfd;
            color: #ffffff;
        }

        QPushButton:disabled,
        QToolButton:disabled {
            background-color: #161b22;
            border-color: #30363d;
            color: #6e7681;
        }

        QPushButton[variant="secondary"],
        QToolButton[variant="secondary"] {
            background-color: #161b22;
            border-color: #30363d;
            color: #c9d1d9;
        }

        QPushButton[accent="true"],
        QToolButton[accent="true"] {
            background-color: #1f6feb;
            border-color: #388bfd;
            color: #ffffff;
        }

        QPushButton[accent="true"]:hover,
        QToolButton[accent="true"]:hover {
            background-color: #388bfd;
            border-color: #58a6ff;
        }

        QLineEdit,
        QSpinBox,
        QDoubleSpinBox,
        QComboBox,
        QDateTimeEdit,
        QTextEdit,
        QPlainTextEdit {
            background-color: #0d1117;
            border: 1px solid #30363d;
            border-radius: 6px;
            min-height: 28px;
            padding: 4px 8px;
            color: #c9d1d9;
            selection-background-color: #1f6feb;
            selection-color: #ffffff;
        }

        QLineEdit:focus,
        QSpinBox:focus,
        QDoubleSpinBox:focus,
        QComboBox:focus,
        QDateTimeEdit:focus,
        QTextEdit:focus,
        QPlainTextEdit:focus {
            border-color: #388bfd;
        }

        QLineEdit[readOnly="true"],
        QTextEdit[readOnly="true"],
        QPlainTextEdit[readOnly="true"] {
            background-color: #161b22;
            color: #8b949e;
        }

        QComboBox::drop-down,
        QDateTimeEdit::drop-down {
            border: 0;
            border-left: 1px solid #30363d;
            width: 26px;
            background-color: #161b22;
            border-top-right-radius: 6px;
            border-bottom-right-radius: 6px;
        }

        QComboBox::down-arrow,
        QDateTimeEdit::down-arrow {
            image: url(__ARROW_DOWN__);
            width: 10px;
            height: 10px;
        }

        QComboBox QAbstractItemView,
        QListView,
        QTreeView {
            background-color: #161b22;
            border: 1px solid #30363d;
            color: #c9d1d9;
            selection-background-color: #1f6feb;
            selection-color: #ffffff;
        }

        QSpinBox::up-button,
        QDoubleSpinBox::up-button,
        QSpinBox::down-button,
        QDoubleSpinBox::down-button {
            background-color: #161b22;
            border-left: 1px solid #30363d;
            width: 18px;
        }

        QSpinBox::up-button,
        QDoubleSpinBox::up-button {
            border-top-right-radius: 6px;
            border-bottom: 1px solid #30363d;
        }

        QSpinBox::down-button,
        QDoubleSpinBox::down-button {
            border-bottom-right-radius: 6px;
        }

        QSpinBox::up-button:hover,
        QDoubleSpinBox::up-button:hover,
        QSpinBox::down-button:hover,
        QDoubleSpinBox::down-button:hover {
            background-color: #21262d;
        }

        QSpinBox::up-arrow,
        QDoubleSpinBox::up-arrow {
            image: url(__ARROW_UP__);
            width: 10px;
            height: 10px;
        }

        QSpinBox::down-arrow,
        QDoubleSpinBox::down-arrow {
            image: url(__ARROW_DOWN__);
            width: 10px;
            height: 10px;
        }

        QCheckBox {
            spacing: 8px;
            color: #c9d1d9;
        }

        QCheckBox::indicator {
            width: 18px;
            height: 18px;
        }

        QCheckBox::indicator:unchecked {
            image: url(__CHECKBOX_UNCHECKED__);
        }

        QCheckBox::indicator:checked {
            image: url(__CHECKBOX_CHECKED__);
        }

        QCheckBox::indicator:unchecked:disabled {
            image: url(__CHECKBOX_UNCHECKED_DISABLED__);
        }

        QCheckBox::indicator:checked:disabled {
            image: url(__CHECKBOX_CHECKED_DISABLED__);
        }

        QTableWidget,
        QTreeWidget {
            background-color: #0d1117;
            alternate-background-color: #161b22;
            border: 1px solid #30363d;
            border-radius: 6px;
            gridline-color: #21262d;
            selection-background-color: #1f6feb;
            selection-color: #ffffff;
        }

        QTableWidget::item,
        QTreeWidget::item {
            border-bottom: 1px solid #21262d;
            padding: 6px;
        }

        QTableWidget::item:selected,
        QTreeWidget::item:selected {
            background-color: #1f6feb;
            color: #ffffff;
        }

        QHeaderView::section,
        QTableCornerButton::section {
            background-color: #161b22;
            border: 0;
            border-bottom: 1px solid #30363d;
            color: #c9d1d9;
            font-weight: 700;
            padding: 8px;
        }

        QListWidget {
            background-color: #0d1117;
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 6px;
        }

        QListWidget::item {
            border-radius: 5px;
            min-height: 28px;
            padding: 5px 8px;
        }

        QListWidget::item:hover {
            background-color: #161b22;
        }

        QListWidget::item:selected {
            background-color: #1f6feb;
            color: #ffffff;
        }

        QMenu {
            background-color: #161b22;
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 6px;
        }

        QMenu::item {
            border-radius: 5px;
            padding: 7px 26px 7px 12px;
        }

        QMenu::item:selected {
            background-color: #1f6feb;
            color: #ffffff;
        }

        QLabel[metric="true"] {
            background-color: #161b22;
            border: 1px solid #30363d;
            border-radius: 6px;
            color: #c9d1d9;
            padding: 12px;
        }

        QLabel#cameraTile {
            background-color: #0d1117;
            border: 1px solid #30363d;
            border-radius: 6px;
            color: #c9d1d9;
        }

        QScrollArea {
            background-color: transparent;
            border: 1px solid #30363d;
            border-radius: 6px;
        }

        QScrollBar:vertical {
            background-color: #0d1117;
            width: 12px;
            border-radius: 6px;
            margin: 2px;
        }

        QScrollBar::handle:vertical {
            background-color: #30363d;
            border-radius: 6px;
            min-height: 24px;
        }

        QScrollBar::handle:vertical:hover {
            background-color: #484f58;
        }

        QScrollBar::sub-line:vertical,
        QScrollBar::add-line:vertical {
            background-color: #161b22;
            border: 1px solid #30363d;
            height: 16px;
            subcontrol-origin: margin;
        }

        QScrollBar::sub-line:vertical {
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            subcontrol-position: top;
        }

        QScrollBar::add-line:vertical {
            border-bottom-left-radius: 6px;
            border-bottom-right-radius: 6px;
            subcontrol-position: bottom;
        }

        QScrollBar::up-arrow:vertical {
            image: url(__ARROW_UP__);
            width: 10px;
            height: 10px;
        }

        QScrollBar::down-arrow:vertical {
            image: url(__ARROW_DOWN__);
            width: 10px;
            height: 10px;
        }

        QScrollBar::add-page:vertical,
        QScrollBar::sub-page:vertical,
        QScrollBar::add-page:horizontal,
        QScrollBar::sub-page:horizontal {
            background: transparent;
        }

        QScrollBar:horizontal {
            background-color: #0d1117;
            height: 12px;
            border-radius: 6px;
            margin: 2px;
        }

        QScrollBar::handle:horizontal {
            background-color: #30363d;
            border-radius: 6px;
            min-width: 24px;
        }

        QScrollBar::handle:horizontal:hover {
            background-color: #484f58;
        }

        QScrollBar::sub-line:horizontal,
        QScrollBar::add-line:horizontal {
            width: 0px;
            border: none;
            background: transparent;
        }

        QTabWidget::pane {
            background-color: #161b22;
            border: 1px solid #30363d;
            border-radius: 6px;
            top: -1px;
        }

        QTabBar::tab {
            background-color: #161b22;
            color: #8b949e;
            border: 1px solid #30363d;
            border-bottom: none;
            padding: 8px 14px;
            margin-right: 4px;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
        }

        QTabBar::tab:selected {
            background-color: #0d1117;
            color: #f0f6fc;
        }

        QTabBar::tab:hover:!selected {
            color: #c9d1d9;
            background-color: #21262d;
        }

        QSplitter::handle {
            background-color: #21262d;
        }

        QToolTip {
            background-color: #161b22;
            border: 1px solid #30363d;
            color: #c9d1d9;
            padding: 6px 8px;
        }

        QStatusBar {
            background-color: #161b22;
            border-top: 1px solid #30363d;
            color: #8b949e;
        }
    """
    app.setStyleSheet(
        stylesheet
        .replace("__ARROW_UP__", arrow_up)
        .replace("__ARROW_DOWN__", arrow_down)
        .replace("__CHECKBOX_UNCHECKED__", checkbox_unchecked)
        .replace("__CHECKBOX_CHECKED__", checkbox_checked)
        .replace("__CHECKBOX_UNCHECKED_DISABLED__", checkbox_unchecked_disabled)
        .replace("__CHECKBOX_CHECKED_DISABLED__", checkbox_checked_disabled)
    )
