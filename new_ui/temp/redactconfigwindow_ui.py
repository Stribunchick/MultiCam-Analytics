# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'redactconfigwindow.ui'
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
from PySide6.QtWidgets import (QAbstractSpinBox, QApplication, QCheckBox, QDoubleSpinBox,
    QGridLayout, QGroupBox, QHBoxLayout, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QPushButton,
    QSizePolicy, QSpacerItem, QToolButton, QVBoxLayout,
    QWidget)

class Ui_redact_config_window(object):
    def setupUi(self, redact_config_window):
        if not redact_config_window.objectName():
            redact_config_window.setObjectName(u"redact_config_window")
        redact_config_window.resize(511, 389)
        self.gridLayout_2 = QGridLayout(redact_config_window)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)

        self.ok_button = QPushButton(redact_config_window)
        self.ok_button.setObjectName(u"ok_button")

        self.horizontalLayout_2.addWidget(self.ok_button)

        self.cancel_button = QPushButton(redact_config_window)
        self.cancel_button.setObjectName(u"cancel_button")

        self.horizontalLayout_2.addWidget(self.cancel_button)


        self.gridLayout_2.addLayout(self.horizontalLayout_2, 1, 1, 1, 1)

        self.verticalLayout_4 = QVBoxLayout()
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.groupBox_4 = QGroupBox(redact_config_window)
        self.groupBox_4.setObjectName(u"groupBox_4")
        self.horizontalLayout_3 = QHBoxLayout(self.groupBox_4)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.active_classes_listWidget = QListWidget(self.groupBox_4)
        self.active_classes_listWidget.setObjectName(u"active_classes_listWidget")

        self.horizontalLayout_3.addWidget(self.active_classes_listWidget)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer_2)

        self.transfer_selected_classes_right = QToolButton(self.groupBox_4)
        self.transfer_selected_classes_right.setObjectName(u"transfer_selected_classes_right")

        self.verticalLayout_2.addWidget(self.transfer_selected_classes_right)

        self.transfer_selected_classes_left = QToolButton(self.groupBox_4)
        self.transfer_selected_classes_left.setObjectName(u"transfer_selected_classes_left")

        self.verticalLayout_2.addWidget(self.transfer_selected_classes_left)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer)


        self.horizontalLayout_3.addLayout(self.verticalLayout_2)

        self.inactive_classes_listWidget = QListWidget(self.groupBox_4)
        self.inactive_classes_listWidget.setObjectName(u"inactive_classes_listWidget")

        self.horizontalLayout_3.addWidget(self.inactive_classes_listWidget)


        self.verticalLayout_4.addWidget(self.groupBox_4)

        self.groupBox_3 = QGroupBox(redact_config_window)
        self.groupBox_3.setObjectName(u"groupBox_3")
        self.horizontalLayout_4 = QHBoxLayout(self.groupBox_3)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.active_cameras_listWidget = QListWidget(self.groupBox_3)
        self.active_cameras_listWidget.setObjectName(u"active_cameras_listWidget")

        self.horizontalLayout_4.addWidget(self.active_cameras_listWidget)

        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_3.addItem(self.verticalSpacer_3)

        self.transfer_selected_cameras_right = QToolButton(self.groupBox_3)
        self.transfer_selected_cameras_right.setObjectName(u"transfer_selected_cameras_right")

        self.verticalLayout_3.addWidget(self.transfer_selected_cameras_right)

        self.transfer_selected_cameras_left = QToolButton(self.groupBox_3)
        self.transfer_selected_cameras_left.setObjectName(u"transfer_selected_cameras_left")

        self.verticalLayout_3.addWidget(self.transfer_selected_cameras_left)

        self.verticalSpacer_4 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_3.addItem(self.verticalSpacer_4)


        self.horizontalLayout_4.addLayout(self.verticalLayout_3)

        self.inactive_cameras_listWidget = QListWidget(self.groupBox_3)
        self.inactive_cameras_listWidget.setObjectName(u"inactive_cameras_listWidget")

        self.horizontalLayout_4.addWidget(self.inactive_cameras_listWidget)


        self.verticalLayout_4.addWidget(self.groupBox_3)


        self.gridLayout_2.addLayout(self.verticalLayout_4, 0, 1, 1, 1)

        self.verticalLayout_5 = QVBoxLayout()
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.label = QLabel(redact_config_window)
        self.label.setObjectName(u"label")

        self.horizontalLayout_5.addWidget(self.label)

        self.config_name_lineEdit = QLineEdit(redact_config_window)
        self.config_name_lineEdit.setObjectName(u"config_name_lineEdit")

        self.horizontalLayout_5.addWidget(self.config_name_lineEdit)


        self.verticalLayout_5.addLayout(self.horizontalLayout_5)

        self.groupBox_2 = QGroupBox(redact_config_window)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.gridLayout = QGridLayout(self.groupBox_2)
        self.gridLayout.setObjectName(u"gridLayout")
        self.label_3 = QLabel(self.groupBox_2)
        self.label_3.setObjectName(u"label_3")

        self.gridLayout.addWidget(self.label_3, 0, 0, 1, 1)

        self.fps_lineEdit = QLineEdit(self.groupBox_2)
        self.fps_lineEdit.setObjectName(u"fps_lineEdit")

        self.gridLayout.addWidget(self.fps_lineEdit, 0, 1, 1, 1)

        self.label_2 = QLabel(self.groupBox_2)
        self.label_2.setObjectName(u"label_2")

        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 1)

        self.cameras_per_row_lineEdit = QLineEdit(self.groupBox_2)
        self.cameras_per_row_lineEdit.setObjectName(u"cameras_per_row_lineEdit")

        self.gridLayout.addWidget(self.cameras_per_row_lineEdit, 1, 1, 1, 1)


        self.verticalLayout_5.addWidget(self.groupBox_2)

        self.groupBox = QGroupBox(redact_config_window)
        self.groupBox.setObjectName(u"groupBox")
        self.verticalLayout = QVBoxLayout(self.groupBox)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.enable_processing_checkBox = QCheckBox(self.groupBox)
        self.enable_processing_checkBox.setObjectName(u"enable_processing_checkBox")

        self.verticalLayout.addWidget(self.enable_processing_checkBox)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label_4 = QLabel(self.groupBox)
        self.label_4.setObjectName(u"label_4")

        self.horizontalLayout.addWidget(self.label_4)

        self.conf_thres_spinbox = QDoubleSpinBox(self.groupBox)
        self.conf_thres_spinbox.setObjectName(u"conf_thres_spinbox")
        self.conf_thres_spinbox.setMaximum(1.000000000000000)
        self.conf_thres_spinbox.setStepType(QAbstractSpinBox.StepType.AdaptiveDecimalStepType)
        self.conf_thres_spinbox.setValue(0.700000000000000)

        self.horizontalLayout.addWidget(self.conf_thres_spinbox)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.verticalLayout_5.addWidget(self.groupBox)

        self.verticalSpacer_5 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_5.addItem(self.verticalSpacer_5)


        self.gridLayout_2.addLayout(self.verticalLayout_5, 0, 0, 1, 1)


        self.retranslateUi(redact_config_window)

        QMetaObject.connectSlotsByName(redact_config_window)
    # setupUi

    def retranslateUi(self, redact_config_window):
        redact_config_window.setWindowTitle(QCoreApplication.translate("redact_config_window", u"\u0420\u0435\u0434\u0430\u043a\u0442\u0438\u0440\u043e\u0432\u0430\u0442\u044c", None))
        self.ok_button.setText(QCoreApplication.translate("redact_config_window", u"\u041e\u043a", None))
        self.cancel_button.setText(QCoreApplication.translate("redact_config_window", u"\u041e\u0442\u043c\u0435\u043d\u0430", None))
        self.groupBox_4.setTitle(QCoreApplication.translate("redact_config_window", u"\u041e\u043f\u0440\u0435\u0434\u0435\u043b\u044f\u0435\u043c\u044b\u0435 \u043a\u043b\u0430\u0441\u0441\u044b", None))
        self.transfer_selected_classes_right.setText(QCoreApplication.translate("redact_config_window", u"<", None))
        self.transfer_selected_classes_left.setText(QCoreApplication.translate("redact_config_window", u">", None))
        self.groupBox_3.setTitle(QCoreApplication.translate("redact_config_window", u"\u0418\u0441\u043f\u043e\u043b\u044c\u0437\u0443\u0435\u043c\u044b\u0435 \u043a\u0430\u043c\u0435\u0440\u044b", None))
        self.transfer_selected_cameras_right.setText(QCoreApplication.translate("redact_config_window", u"<", None))
        self.transfer_selected_cameras_left.setText(QCoreApplication.translate("redact_config_window", u">", None))
        self.label.setText(QCoreApplication.translate("redact_config_window", u"\u0418\u043c\u044f", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("redact_config_window", u"\u041d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0430 \u0432\u0438\u0434\u0435\u043e\u0441\u0442\u0435\u043d\u044b", None))
        self.label_3.setText(QCoreApplication.translate("redact_config_window", u"\u0427\u0430\u0441\u0442\u043e\u0442\u0430 \u043e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u0438\u044f", None))
        self.label_2.setText(QCoreApplication.translate("redact_config_window", u"\u041a\u0430\u043c\u0435\u0440 \u0432 \u0440\u044f\u0434\u0443", None))
        self.groupBox.setTitle(QCoreApplication.translate("redact_config_window", u"\u041d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0430 \u043e\u0431\u0440\u0430\u0431\u043e\u0442\u043a\u0438", None))
        self.enable_processing_checkBox.setText(QCoreApplication.translate("redact_config_window", u"\u0412\u043a\u043b\u044e\u0447\u0438\u0442\u044c \u043e\u0431\u0440\u0430\u0431\u043e\u0442\u043a\u0443", None))
        self.label_4.setText(QCoreApplication.translate("redact_config_window", u"\u041f\u043e\u0440\u043e\u0433 \u0443\u0432\u0435\u0440\u0435\u043d\u043d\u043e\u0441\u0442\u0438", None))
    # retranslateUi

