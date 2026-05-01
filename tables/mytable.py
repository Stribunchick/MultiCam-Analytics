from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QAbstractItemView, QMenu, QTableWidget, QVBoxLayout, QWidget


class MyTable(QWidget):
    add_requested = Signal()
    edit_requested = Signal(int)
    delete_requested = Signal(int, str)
    run_videowall_requested = Signal(int)

    def __init__(self, show_videowall=False, allow_add=True, allow_edit=True, allow_delete=True):
        super().__init__()
        self.show_videowall = show_videowall
        self.allow_add = allow_add
        self.allow_edit = allow_edit
        self.allow_delete = allow_delete

        self.table = QTableWidget()
        self.initialize_table()
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.layout().addWidget(self.table)

    def initialize_table(self):
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(38)
        self.table.horizontalHeader().setHighlightSections(False)

    def show_context_menu(self, pos):
        menu = QMenu(self)

        add_action = menu.addAction("Добавить") if self.allow_add else None
        edit_action = menu.addAction("Редактировать") if self.allow_edit else None
        delete_action = menu.addAction("Удалить") if self.allow_delete else None

        row = self.table.rowAt(pos.y())

        if row >= 0:
            self.table.selectRow(row)

        if row < 0 and edit_action is not None:
            edit_action.setVisible(False)
        if row < 0 and delete_action is not None:
            delete_action.setVisible(False)
        if edit_action is not None:
            edit_action.setEnabled(row >= 0)
        if delete_action is not None:
            delete_action.setEnabled(row >= 0)

        if self.show_videowall:
            run_action = menu.addAction("Запустить видеостену")
            run_action.setEnabled(row >= 0)
        else:
            run_action = None

        action = menu.exec(self.table.mapToGlobal(pos))
        if add_action is not None and action == add_action:
            self.add_requested.emit()
        elif edit_action is not None and action == edit_action and row >= 0:
            record_id = int(self.table.item(row, 0).text())
            self.edit_requested.emit(record_id)
        elif delete_action is not None and action == delete_action and row >= 0:
            record_id = int(self.table.item(row, 0).text())
            record_name = self.table.item(row, 1).text()
            self.delete_requested.emit(record_id, record_name)
        elif run_action is not None and action == run_action and row >= 0:
            record_id = int(self.table.item(row, 0).text())
            self.run_videowall_requested.emit(record_id)
