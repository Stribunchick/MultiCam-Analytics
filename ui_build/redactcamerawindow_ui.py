# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'redactcamerawindow.ui'
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
    QLabel, QLineEdit, QPushButton, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget)

class Ui_camera_redact_window(object):
    def setupUi(self, camera_redact_window):
        if not camera_redact_window.objectName():
            camera_redact_window.setObjectName(u"camera_redact_window")
        camera_redact_window.resize(335, 239)
        self.gridLayout_2 = QGridLayout(camera_redact_window)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.groupBox = QGroupBox(camera_redact_window)
        self.groupBox.setObjectName(u"groupBox")
        self.gridLayout = QGridLayout(self.groupBox)
        self.gridLayout.setObjectName(u"gridLayout")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label = QLabel(self.groupBox)
        self.label.setObjectName(u"label")

        self.horizontalLayout.addWidget(self.label)

        self.camera_name_lineEdit = QLineEdit(self.groupBox)
        self.camera_name_lineEdit.setObjectName(u"camera_name_lineEdit")

        self.horizontalLayout.addWidget(self.camera_name_lineEdit)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.label_4 = QLabel(self.groupBox)
        self.label_4.setObjectName(u"label_4")

        self.horizontalLayout_2.addWidget(self.label_4)

        self.location_lineEdit = QLineEdit(self.groupBox)
        self.location_lineEdit.setObjectName(u"location_lineEdit")

        self.horizontalLayout_2.addWidget(self.location_lineEdit)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.label_5 = QLabel(self.groupBox)
        self.label_5.setObjectName(u"label_5")

        self.horizontalLayout_5.addWidget(self.label_5)

        self.username_lineEdit = QLineEdit(self.groupBox)
        self.username_lineEdit.setObjectName(u"username_lineEdit")

        self.horizontalLayout_5.addWidget(self.username_lineEdit)


        self.verticalLayout.addLayout(self.horizontalLayout_5)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.label_2 = QLabel(self.groupBox)
        self.label_2.setObjectName(u"label_2")

        self.horizontalLayout_3.addWidget(self.label_2)

        self.ip_lineEdit = QLineEdit(self.groupBox)
        self.ip_lineEdit.setObjectName(u"ip_lineEdit")

        self.horizontalLayout_3.addWidget(self.ip_lineEdit)


        self.verticalLayout.addLayout(self.horizontalLayout_3)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.label_3 = QLabel(self.groupBox)
        self.label_3.setObjectName(u"label_3")

        self.horizontalLayout_4.addWidget(self.label_3)

        self.password_lineEdit = QLineEdit(self.groupBox)
        self.password_lineEdit.setObjectName(u"password_lineEdit")

        self.horizontalLayout_4.addWidget(self.password_lineEdit)


        self.verticalLayout.addLayout(self.horizontalLayout_4)


        self.gridLayout.addLayout(self.verticalLayout, 0, 0, 1, 1)


        self.gridLayout_2.addWidget(self.groupBox, 0, 0, 1, 2)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_2.addItem(self.horizontalSpacer, 1, 0, 1, 1)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.ok_button = QPushButton(camera_redact_window)
        self.ok_button.setObjectName(u"ok_button")

        self.horizontalLayout_6.addWidget(self.ok_button)

        self.cancel_button = QPushButton(camera_redact_window)
        self.cancel_button.setObjectName(u"cancel_button")

        self.horizontalLayout_6.addWidget(self.cancel_button)


        self.gridLayout_2.addLayout(self.horizontalLayout_6, 1, 1, 1, 1)


        self.retranslateUi(camera_redact_window)

        QMetaObject.connectSlotsByName(camera_redact_window)
    # setupUi

    def retranslateUi(self, camera_redact_window):
        camera_redact_window.setWindowTitle(QCoreApplication.translate("camera_redact_window", u"\u0420\u0435\u0434\u0430\u043a\u0442\u0438\u0440\u043e\u0432\u0430\u043d\u0438\u0435 \u043a\u0430\u043c\u0435\u0440\u044b", None))
        self.groupBox.setTitle(QCoreApplication.translate("camera_redact_window", u"\u0414\u0430\u043d\u043d\u044b\u0435 \u043e \u043a\u0430\u043c\u0435\u0440\u0435", None))
        self.label.setText(QCoreApplication.translate("camera_redact_window", u"\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435 \u043a\u0430\u043c\u0435\u0440\u044b", None))
        self.label_4.setText(QCoreApplication.translate("camera_redact_window", u"\u041c\u0435\u0441\u0442\u043e\u043f\u043e\u043b\u043e\u0436\u0435\u043d\u0438\u0435", None))
        self.label_5.setText(QCoreApplication.translate("camera_redact_window", u"\u041b\u043e\u0433\u0438\u043d", None))
        self.label_2.setText(QCoreApplication.translate("camera_redact_window", u"IP-\u0430\u0434\u0440\u0435\u0441", None))
        self.label_3.setText(QCoreApplication.translate("camera_redact_window", u"\u041f\u0430\u0440\u043e\u043b\u044c", None))
        self.ok_button.setText(QCoreApplication.translate("camera_redact_window", u"\u041e\u043a", None))
        self.cancel_button.setText(QCoreApplication.translate("camera_redact_window", u"\u041e\u0442\u043c\u0435\u043d\u0430", None))
    # retranslateUi

