# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'mainconfigwindow.ui'
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
    QMainWindow, QPushButton, QSizePolicy, QSpacerItem,
    QStatusBar, QVBoxLayout, QWidget)

class Ui_main_config_window(object):
    def setupUi(self, main_config_window):
        if not main_config_window.objectName():
            main_config_window.setObjectName(u"main_config_window")
        main_config_window.resize(446, 304)
        self.centralwidget = QWidget(main_config_window)
        self.centralwidget.setObjectName(u"centralwidget")
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.buttons_groupBox = QGroupBox(self.centralwidget)
        self.buttons_groupBox.setObjectName(u"buttons_groupBox")
        self.horizontalLayout = QHBoxLayout(self.buttons_groupBox)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.camera_manage_button = QPushButton(self.buttons_groupBox)
        self.camera_manage_button.setObjectName(u"camera_manage_button")

        self.horizontalLayout.addWidget(self.camera_manage_button)

        self.model_manage_button = QPushButton(self.buttons_groupBox)
        self.model_manage_button.setObjectName(u"model_manage_button")

        self.horizontalLayout.addWidget(self.model_manage_button)


        self.horizontalLayout_2.addWidget(self.buttons_groupBox)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.config_table_groupbox = QGroupBox(self.centralwidget)
        self.config_table_groupbox.setObjectName(u"config_table_groupbox")

        self.verticalLayout.addWidget(self.config_table_groupbox)


        self.gridLayout.addLayout(self.verticalLayout, 0, 0, 1, 1)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout.addItem(self.verticalSpacer, 1, 0, 1, 1)

        main_config_window.setCentralWidget(self.centralwidget)
        self.statusbar = QStatusBar(main_config_window)
        self.statusbar.setObjectName(u"statusbar")
        main_config_window.setStatusBar(self.statusbar)

        self.retranslateUi(main_config_window)

        QMetaObject.connectSlotsByName(main_config_window)
    # setupUi

    def retranslateUi(self, main_config_window):
        main_config_window.setWindowTitle(QCoreApplication.translate("main_config_window", u"\u041e\u043a\u043d\u043e \u043a\u043e\u043d\u0444\u0438\u0433\u0443\u0440\u0430\u0446\u0438\u0438", None))
        self.buttons_groupBox.setTitle("")
        self.camera_manage_button.setText(QCoreApplication.translate("main_config_window", u"\u0423\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0438\u0435 \u043a\u0430\u043c\u0435\u0440\u0430\u043c\u0438", None))
        self.model_manage_button.setText(QCoreApplication.translate("main_config_window", u"\u0423\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0438\u0435 \u043c\u043e\u0434\u0435\u043b\u044f\u043c\u0438", None))
        self.config_table_groupbox.setTitle("")
    # retranslateUi

