# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'modelmanagerwindow.ui'
##
## Created by: Qt User Interface Compiler version 6.9.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QGridLayout, QGroupBox, QHBoxLayout,
    QPushButton, QSizePolicy, QSpacerItem, QWidget)

class Ui_models_manager_window(object):
    def setupUi(self, models_manager_window):
        if not models_manager_window.objectName():
            models_manager_window.setObjectName(u"models_manager_window")
        models_manager_window.resize(382, 235)
        self.gridLayout = QGridLayout(models_manager_window)
        self.gridLayout.setObjectName(u"gridLayout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer, 2, 0, 1, 1)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.ok_button = QPushButton(models_manager_window)
        self.ok_button.setObjectName(u"ok_button")

        self.horizontalLayout.addWidget(self.ok_button)

        self.cancel_button = QPushButton(models_manager_window)
        self.cancel_button.setObjectName(u"cancel_button")

        self.horizontalLayout.addWidget(self.cancel_button)


        self.gridLayout.addLayout(self.horizontalLayout, 2, 1, 1, 1)

        self.models_table_groupBox = QGroupBox(models_manager_window)
        self.models_table_groupBox.setObjectName(u"models_table_groupBox")

        self.gridLayout.addWidget(self.models_table_groupBox, 0, 0, 1, 2)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout.addItem(self.verticalSpacer, 1, 1, 1, 1)


        self.retranslateUi(models_manager_window)

        QMetaObject.connectSlotsByName(models_manager_window)
    # setupUi

    def retranslateUi(self, models_manager_window):
        models_manager_window.setWindowTitle(QCoreApplication.translate("models_manager_window", u"\u0423\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0438\u0435 \u043c\u043e\u0434\u0435\u043b\u044f\u043c\u0438 \u0440\u0430\u0441\u043f\u043e\u0437\u043d\u0430\u0432\u0430\u043d\u0438\u044f", None))
        self.ok_button.setText(QCoreApplication.translate("models_manager_window", u"\u041e\u043a", None))
        self.cancel_button.setText(QCoreApplication.translate("models_manager_window", u"\u041e\u0442\u043c\u0435\u043d\u0430", None))
        self.models_table_groupBox.setTitle("")
    # retranslateUi

