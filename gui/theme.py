from PySide6.QtGui import QFont


def apply_theme(app):
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))
    app.setStyleSheet("""
        QWidget {
            background-color: #f4f7fb;
            color: #1f2937;
            font-family: "Segoe UI", Arial, sans-serif;
            font-size: 10pt;
        }

        QMainWindow,
        QDialog {
            background-color: #f4f7fb;
        }

        QLabel#pageTitle {
            color: #111827;
            font-size: 20pt;
            font-weight: 700;
        }

        QLabel#pageSubtitle {
            color: #64748b;
            font-size: 10pt;
        }

        QGroupBox {
            background-color: #ffffff;
            border: 1px solid #dbe3ef;
            border-radius: 8px;
            margin-top: 10px;
            padding: 12px;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 6px;
            color: #475569;
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
            background-color: #1d4ed8;
        }

        QPushButton:pressed {
            background-color: #1e40af;
        }

        QPushButton:disabled {
            background-color: #cbd5e1;
            border-color: #cbd5e1;
            color: #64748b;
        }

        QPushButton[variant="secondary"] {
            background-color: #ffffff;
            border-color: #cbd5e1;
            color: #1f2937;
        }

        QPushButton[variant="secondary"]:hover {
            background-color: #eef4ff;
            border-color: #93b4f8;
            color: #1d4ed8;
        }

        QLineEdit,
        QSpinBox,
        QDoubleSpinBox,
        QComboBox,
        QDateTimeEdit {
            background-color: #ffffff;
            border: 1px solid #cbd5e1;
            border-radius: 6px;
            min-height: 28px;
            padding: 4px 8px;
            selection-background-color: #bfdbfe;
        }

        QLineEdit:focus,
        QSpinBox:focus,
        QDoubleSpinBox:focus,
        QComboBox:focus,
        QDateTimeEdit:focus {
            border-color: #2563eb;
        }

        QComboBox::drop-down,
        QDateTimeEdit::drop-down {
            border: 0;
            width: 24px;
        }

        QCheckBox {
            spacing: 8px;
        }

        QCheckBox::indicator {
            width: 16px;
            height: 16px;
            border: 1px solid #94a3b8;
            border-radius: 4px;
            background: #ffffff;
        }

        QCheckBox::indicator:checked {
            background-color: #2563eb;
            border-color: #2563eb;
        }

        QTableWidget {
            background-color: #ffffff;
            alternate-background-color: #f8fafc;
            border: 1px solid #dbe3ef;
            border-radius: 8px;
            gridline-color: #e5eaf2;
            selection-background-color: #dbeafe;
            selection-color: #111827;
        }

        QTableWidget::item {
            border-bottom: 1px solid #eef2f7;
            padding: 6px;
        }

        QTableWidget::item:selected {
            background-color: #dbeafe;
            color: #111827;
        }

        QHeaderView::section {
            background-color: #eef4ff;
            border: 0;
            border-bottom: 1px solid #c7d2fe;
            color: #334155;
            font-weight: 700;
            padding: 8px;
        }

        QListWidget {
            background-color: #ffffff;
            border: 1px solid #dbe3ef;
            border-radius: 8px;
            padding: 6px;
        }

        QListWidget::item {
            border-radius: 5px;
            min-height: 28px;
            padding: 5px 8px;
        }

        QListWidget::item:selected {
            background-color: #dbeafe;
            color: #111827;
        }

        QMenu {
            background-color: #ffffff;
            border: 1px solid #dbe3ef;
            border-radius: 6px;
            padding: 6px;
        }

        QMenu::item {
            border-radius: 5px;
            padding: 7px 26px 7px 12px;
        }

        QMenu::item:selected {
            background-color: #eef4ff;
            color: #1d4ed8;
        }

        QLabel[metric="true"] {
            background-color: #ffffff;
            border: 1px solid #dbe3ef;
            border-radius: 8px;
            color: #334155;
            padding: 12px;
        }

        QLabel#cameraTile {
            background-color: #0f172a;
            border: 1px solid #334155;
            border-radius: 8px;
            color: #e2e8f0;
        }

        QStatusBar {
            background-color: #eef4ff;
            color: #475569;
        }
    """)
