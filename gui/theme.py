from PySide6.QtGui import QFont


def apply_theme(app):
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))
    app.setStyleSheet("""
        QWidget {
            background-color: #0b1220;
            color: #e5edf7;
            font-family: "Segoe UI", Arial, sans-serif;
            font-size: 10pt;
        }

        QMainWindow,
        QDialog {
            background-color: #0b1220;
        }

        QLabel#pageTitle {
            color: #f8fafc;
            font-size: 20pt;
            font-weight: 700;
        }

        QLabel#pageSubtitle {
            color: #94a3b8;
            font-size: 10pt;
        }

        QGroupBox {
            background-color: #111827;
            border: 1px solid #243244;
            border-radius: 8px;
            margin-top: 10px;
            padding: 12px;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 6px;
            color: #a8b4c7;
            font-weight: 600;
        }

        QPushButton {
            background-color: #2563eb;
            border: 1px solid #1d4ed8;
            border-radius: 7px;
            color: #ffffff;
            font-weight: 600;
            min-height: 30px;
            padding: 7px 14px;
        }

        QPushButton:hover {
            background-color: #3b82f6;
        }

        QPushButton:pressed {
            background-color: #1e40af;
        }

        QPushButton:disabled {
            background-color: #334155;
            border-color: #334155;
            color: #94a3b8;
        }

        QPushButton[variant="secondary"] {
            background-color: #172033;
            border-color: #314055;
            color: #dbe7f5;
        }

        QPushButton[variant="secondary"]:hover {
            background-color: #1d2a40;
            border-color: #4f78c7;
            color: #93c5fd;
        }

        QLineEdit,
        QSpinBox,
        QDoubleSpinBox,
        QComboBox,
        QDateTimeEdit {
            background-color: #0f172a;
            border: 1px solid #334155;
            border-radius: 6px;
            min-height: 28px;
            padding: 4px 8px;
            selection-background-color: #1d4ed8;
            selection-color: #eff6ff;
        }

        QLineEdit:focus,
        QSpinBox:focus,
        QDoubleSpinBox:focus,
        QComboBox:focus,
        QDateTimeEdit:focus {
            border-color: #60a5fa;
        }

        QComboBox::drop-down,
        QDateTimeEdit::drop-down {
            border: 0;
            width: 24px;
        }

        QComboBox QAbstractItemView {
            background-color: #111827;
            border: 1px solid #334155;
            color: #e5edf7;
            selection-background-color: #1d4ed8;
            selection-color: #eff6ff;
        }

        QCheckBox {
            spacing: 8px;
        }

        QCheckBox::indicator {
            width: 16px;
            height: 16px;
            border: 1px solid #64748b;
            border-radius: 4px;
            background: #0f172a;
        }

        QCheckBox::indicator:checked {
            background-color: #2563eb;
            border-color: #2563eb;
        }

        QTableWidget {
            background-color: #0f172a;
            alternate-background-color: #111827;
            border: 1px solid #243244;
            border-radius: 8px;
            gridline-color: #1f2937;
            selection-background-color: #1d4ed8;
            selection-color: #eff6ff;
        }

        QTableWidget::item {
            border-bottom: 1px solid #1f2937;
            padding: 6px;
        }

        QTableWidget::item:selected {
            background-color: #1d4ed8;
            color: #eff6ff;
        }

        QHeaderView::section {
            background-color: #172033;
            border: 0;
            border-bottom: 1px solid #314055;
            color: #dbe7f5;
            font-weight: 700;
            padding: 8px;
        }

        QListWidget {
            background-color: #0f172a;
            border: 1px solid #243244;
            border-radius: 8px;
            padding: 6px;
        }

        QListWidget::item {
            border-radius: 5px;
            min-height: 28px;
            padding: 5px 8px;
        }

        QListWidget::item:selected {
            background-color: #1d4ed8;
            color: #eff6ff;
        }

        QMenu {
            background-color: #111827;
            border: 1px solid #243244;
            border-radius: 6px;
            padding: 6px;
        }

        QMenu::item {
            border-radius: 5px;
            padding: 7px 26px 7px 12px;
        }

        QMenu::item:selected {
            background-color: #1d4ed8;
            color: #eff6ff;
        }

        QLabel[metric="true"] {
            background-color: #111827;
            border: 1px solid #243244;
            border-radius: 8px;
            color: #dbe7f5;
            padding: 12px;
        }

        QLabel#cameraTile {
            background-color: #0f172a;
            border: 1px solid #334155;
            border-radius: 8px;
            color: #e2e8f0;
        }

        QScrollArea {
            background-color: #0b1220;
            border: 1px solid #243244;
            border-radius: 8px;
        }

        QToolTip {
            background-color: #111827;
            border: 1px solid #334155;
            color: #e5edf7;
            padding: 6px 8px;
        }

        QStatusBar {
            background-color: #111827;
            color: #94a3b8;
        }
    """)
